# Copyright (c) 2017-2019 Datasud.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.gis import admin as geo_admin
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone

from auth_users.forms.account import DeleteAdminForm
from idgo_admin.ckan_module import CkanHandler
from idgo_admin.models import AccountActions
from idgo_admin.models import Dataset
from idgo_admin.models import LiaisonsContributeurs
from idgo_admin.models import LiaisonsReferents
from idgo_admin.models.mail import send_account_creation_mail
from idgo_admin.models import Organisation

import random
import string

User = get_user_model()

geo_admin.GeoModelAdmin.default_lon = 160595
geo_admin.GeoModelAdmin.default_lat = 5404331
geo_admin.GeoModelAdmin.default_zoom = 14


# admin.site.unregister(Group)
# admin.site.unregister(User)


class CustomLiaisonsReferentsModelForm(forms.ModelForm):

    model = LiaisonsReferents
    fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organisation'].queryset = Organisation.objects.filter(is_active=True)


class CustomLiaisonsContributeursModelForm(forms.ModelForm):

    model = LiaisonsContributeurs
    fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organisation'].queryset = Organisation.objects.filter(is_active=True)
        self.fields['organisation'].initial = None


class LiaisonReferentsInline(admin.TabularInline):
    model = LiaisonsReferents
    form = CustomLiaisonsReferentsModelForm
    extra = 0
    verbose_name_plural = \
        "Organisations pour lesquelles l'utilisateur est référent technique"
    verbose_name = 'Organisation'


class LiaisonsContributeursInline(admin.TabularInline):
    model = LiaisonsContributeurs
    form = CustomLiaisonsContributeursModelForm
    extra = 0
    verbose_name_plural = \
        "Organisations pour lesquelles l'utilisateur est contributeur"
    verbose_name = 'Organisation'


class AccountActionsInline(admin.TabularInline):
    model = AccountActions
    verbose_name_plural = 'Actions de validation'
    verbose_name = 'Action de validation'
    ordering = ['closed', 'created_on']
    can_delete = False
    extra = 0
    fields = [
        'action', 'change_link', 'closed', 'created_on', 'orga_name']
    readonly_fields = [
        'action', 'change_link', 'closed', 'created_on', 'orga_name']

    def has_add_permission(self, request, obj=None):
        return False

    def change_link(self, obj):
        # Si extra != 0 les instances supplémentaires se voient attribuer une url
        # par sécurité on empeche d'afficher un lien si pas d'instance.
        if obj.pk:
            # get_path ne définissant pas d'url pour une action de ce type
            if obj.action == 'created_organisation_through_api':
                mark = '<div>N/A</div>'
            else:
                mark = '<a href="{}">Valider l\'action</a>'.format(obj.get_path())
            return mark_safe(mark)
    change_link.short_description = 'Lien de validation'


# class UserAddForm(forms.ModelForm):
#
#     class Meta(object):
#         model = User
#         fields = '__all__'
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#     def clean(self):
#         self.cleaned_data.update(is_active=True)
#         if self.cleaned_data.get('organisation'):
#             self.cleaned_data.update(membership=True)
#         if not self.cleaned_data.get('organisation') and self.cleaned_data.get('membership'):
#             raise forms.ValidationError((
#                 'Un utilisateur sans organisation de rattachement '
#                 'ne peut avoir son état de rattachement confirmé.'))
#         return self.cleaned_data


class BaseUserChangeForm(forms.ModelForm):

    class Meta(object):
        model = User
        fields = '__all__'

    def clean(self):
        if not self.cleaned_data.get('organisation') and self.cleaned_data.get('membership'):
            raise forms.ValidationError("Un utilisateur sans organisation de rattachement ne peut avoir son état de rattachement confirmé.")
        return self.cleaned_data


class CrigeUserChangeForm(BaseUserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class StandardUserChangeForm(BaseUserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['crige_membership'].widget = forms.HiddenInput()


class MyUserChangeForm(UserChangeForm):

    class Meta(object):
        model = User
        fields = '__all__'

    def clean(self):
        if 'email' in self.changed_data:
            email = self.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('Cette adresse est reservée.')
        return self.cleaned_data

    def save(self, commit=True, *args, **kwargs):
        user = super().save(commit=False)
        try:
            CkanHandler.update_user(user)
        except Exception as e:
            raise forms.ValidationError(
                "La modification de l'utilisateur sur CKAN a échoué: {}.".format(e))
        if commit:
            user.save()
        return user


class MyUserCreationForm(UserCreationForm):

    class Meta(object):
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'username',
            'crige_membership',
            'is_active',
            'is_admin',
            'membership',
            'organisation',
            'phone',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['password1'].required = False
        self.fields['password2'].required = False

    def clean(self):
        self.cleaned_data.update(is_active=True)
        if self.cleaned_data.get('organisation'):
            self.cleaned_data.update(membership=True)
        if not self.cleaned_data.get('organisation') and self.cleaned_data.get('membership'):
            raise forms.ValidationError((
                'Un utilisateur sans organisation de rattachement '
                'ne peut avoir son état de rattachement confirmé.'))
        self.cleaned_data['password1'] = 'new_password_will_be_generated'
        self.cleaned_data['password2'] = 'new_password_will_be_generated'
        return self.cleaned_data

    def password_generator(self, N=8):
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists() or CkanHandler.is_user_exists(username):
            raise forms.ValidationError("Ce nom d'utilisateur est réservé.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Cette adresse est réservée.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', 'new_password_will_be_generated')
        password2 = self.cleaned_data.get('password2', 'new_password_will_be_generated')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'], code='password_mismatch')

    def save(self, commit=True, *args, **kwargs):
        user = super().save(commit=False)
        pass_generated = self.password_generator()
        try:
            CkanHandler.add_user(user, pass_generated, state='active')
        except Exception as e:
            raise ValidationError(
                "L'ajout de l'utilisateur sur CKAN a échoué: {}.".format(e))
        user.set_password(pass_generated)
        if commit:
            user.save()
        return user


class UserAdmin(AuthUserAdmin):
    add_form = MyUserCreationForm
    form = MyUserChangeForm

    list_display = ['username', 'full_name', 'is_superuser', 'is_admin', 'is_active', 'delete_account_action']
    list_display_links = ['username']
    search_fields = ['last_name', 'username']
    ordering = ['last_name', 'first_name']

    inlines = (LiaisonReferentsInline, LiaisonsContributeursInline, AccountActionsInline)

    prepopulated_fields = {'username': ['first_name', 'last_name']}
    add_fieldsets = [
        (None, {
            'classes': ['wide'],
            'fields': ['first_name', 'last_name', 'username', 'email']})]

    def get_form(self, request, obj=None, **kwargs):
        user = request.user
        if user.is_superuser:
            Form = CrigeUserChangeForm
        else:
            Form = user.is_crige_admin and CrigeUserChangeForm or StandardUserChangeForm
        if obj:
            return Form
        else:
            return super().get_form(request, obj=None, **kwargs)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def full_name(self, obj):
        return ' '.join((obj.last_name.upper(), obj.first_name.capitalize()))
    full_name.short_description = 'Nom et prénom'

    def create_related_liason_contrib(self, instance):
        try:
            LiaisonsContributeurs.objects.get(
                organisation=instance.organisation, user=instance)
        except LiaisonsContributeurs.DoesNotExist:
            LiaisonsContributeurs.objects.create(
                organisation=instance.organisation, user=instance,
                validated_on=timezone.now().date())

    def current_instance_is_new(self, instance):
        try:
            LiaisonsContributeurs.objects.get(
                organisation=instance.organisation, user=instance)
        except LiaisonsContributeurs.DoesNotExist:
            return True
        return False

    def save_formset(self, request, form, formset, change):
        # Si les TabularInlines ne concernent pas les Liaisons Orga
        if formset.model not in (LiaisonsReferents, LiaisonsContributeurs, ):
            return super().save_formset(request, form, formset, change)

        # On s'occupe d'abord des Contributeur pour eviter les doublons
        if formset.model is LiaisonsContributeurs:
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            for instance in instances:
                if self.current_instance_is_new(instance):
                    instance.validated_on = timezone.now().date()
                    instance.save()

        # On crée une liaison contributeur pour chaque liaison référent demandé dans l'admin
        if formset.model is LiaisonsReferents:
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            for instance in instances:
                instance.validated_on = timezone.now().date()
                instance.save()
                self.create_related_liason_contrib(instance)

        formset.save_m2m()

    def save_model(self, request, obj, form, change):
        # Uniquement lors d'une creation
        if not change:
            action = AccountActions.objects.create(
                user=obj, action='set_password_admin')
            url = request.build_absolute_uri(reverse(
                'idgo_admin:password_manager', kwargs={
                    'process': 'initiate', 'key': action.key}))
            send_account_creation_mail(obj, url)
        super().save_model(request, obj, form, change)

    def process_action(self, request, user_id, action_form, action_title):

        user = self.get_object(request, user_id)
        related_datasets = Dataset.objects.filter(editor=user)

        if request.method != 'POST':
            form = action_form(
                include={
                    'user_id': user.id,
                    'related_datasets': related_datasets})
        else:
            form = action_form(
                request.POST,
                include={
                    'user_id': user.id,
                    'related_datasets': related_datasets})
            if form.is_valid():
                form.delete_controller(user, form.cleaned_data.get("new_user"), related_datasets)
                self.message_user(
                    request, 'Le compte utilisateur a bien été supprimé.')
                url = reverse(
                    'admin:idgo_admin_profile_changelist',
                    current_app=self.admin_site.name)
                return HttpResponseRedirect(url)

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['user'] = user
        context['title'] = action_title
        context['related_datasets'] = related_datasets

        return TemplateResponse(
            request, 'admin/idgo_admin/user_action.html', context)

    def process_deleting(self, request, user_id, *args, **kwargs):
        return self.process_action(
            request=request,
            user_id=user_id,
            action_form=DeleteAdminForm,
            action_title="Suppression d'un compte utilisateur")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [url(
            '^(?P<user_id>.+)/delete-account/$',
            self.admin_site.admin_view(self.process_deleting),
            name='delete-account')]
        return custom_urls + urls

    def delete_account_action(self, obj):
        return format_html(
            '<a class="button" href="{}">Supprimer</a>&nbsp;',
            reverse('admin:delete-account', args=[obj.pk]))

    delete_account_action.short_description = 'Supprimer'
    delete_account_action.allow_tags = True


admin.site.register(User, UserAdmin)
