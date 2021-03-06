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


from api.utils import parse_request
from collections import OrderedDict
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db import transaction
from django.http import Http404
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from functools import reduce
from idgo_admin.ckan_module import CkanHandler
from idgo_admin.exceptions import CkanBaseError
from idgo_admin.exceptions import GenericException
from auth_users.forms.account import SignUpForm
from auth_users.forms.account import UpdateAccountForm
from idgo_admin.models import Organisation
from operator import iand
from operator import ior
from rest_framework import permissions
from rest_framework.views import APIView

User = get_user_model()


def serialize(user):

    def nullify(m):
        return m or None

    try:
        return OrderedDict([
            # Information de base sur l'utilisateur
            ('username', user.username),
            ('first_name', user.first_name),
            ('last_name', user.last_name),
            ('admin', user.is_admin),
            ('crige', user.crige_membership),
            # Organisation de rattachement de l'utilisateur
            ('organisation', user.organisation and OrderedDict([
                ('name', user.organisation.slug),
                ('legal_name', user.organisation.legal_name)
                ]) or None),
            # Listes des organisations pour lesquelles l'utilisateur est référent
            ('referent', nullify([OrderedDict([
                ('name', organisation.slug),
                ('legal_name', organisation.legal_name)
                ]) for organisation in user.referent_for])),
            # Listes des organisations pour lesquelles l'utilisateur est contributeur
            ('contribute', nullify([OrderedDict([
                ('name', organisation.slug),
                ('legal_name', organisation.legal_name)
                ]) for organisation in user.contribute_for]))
            ])
    except Exception as e:
        if e.__class__.__name__ == 'RelatedObjectDoesNotExist':
            return None
        raise e


def user_list(order_by='last_name', or_clause=None, **and_clause):

    l1 = [Q(**{k: v}) for k, v in and_clause.items()]
    if or_clause:
        l2 = [Q(**{k: v}) for k, v in or_clause.items()]
        filter = ior(reduce(iand, l1), reduce(iand, l2))
    else:
        filter = reduce(iand, l1)

    return [serialize(user) for user in User.objects.filter(filter).order_by(order_by)]


def handler_get_request(request):
    qs = request.GET.dict()
    or_clause = dict()

    user = request.user
    if user.is_admin:
        # Un administrateur « métiers » peut tout voir.
        pass
    elif user.is_referent:
        # Un référent « métiers » peut voir les utilisateurs des
        # organisations pour lesquelles il est référent.
        qs.update({'organisation__in': user.referent_for})
        or_clause.update({'username': user.username})
    else:
        # L'utilisateur peut se voir lui même.
        qs.update({'username': user.username})

    return user_list(**qs)


def handle_pust_request(request, username=None):

    user = None
    if username:
        user = get_object_or_404(User, username=username)

    query_data = getattr(request, request.method)  # QueryDict

    # `first_name` est obligatoire
    first_name = query_data.pop('first_name', user and [user.first_name])
    if first_name:
        query_data.__setitem__('first_name', first_name[-1])

    # `last_name` est obligatoire
    last_name = query_data.pop('last_name', user and [user.last_name])
    if last_name:
        query_data.__setitem__('last_name', last_name[-1])

    # `email` est obligatoire
    email = query_data.pop('email', user and [user.email])
    if email:
        query_data.__setitem__('email', email[-1])

    # organisation
    organisation_slug = query_data.pop('organisation', None)
    if organisation_slug:
        try:
            organisation = Organisation.objects.get(slug=organisation_slug[-1])
        except Organisation.DoesNotExist as e:
            raise GenericException(details=e.__str__())
    elif user and user.profile:
        organisation = user.profile.organisation
    else:
        organisation = None
    if organisation:
        query_data.__setitem__('organisation', organisation.pk)

    password = query_data.pop('password', None)
    if password:
        query_data.__setitem__('password1', password[-1])
        query_data.__setitem__('password2', password[-1])

    if user:
        form = UpdateAccountForm(query_data, instance=user)
    else:
        form = SignUpForm(query_data, unlock_terms=True)
    if not form.is_valid():
        raise GenericException(details=form._errors)
    try:
        with transaction.atomic():
            if user:
                phone = form.cleaned_data.pop('phone', None)
                for k, v in form.cleaned_data.items():
                    if k == 'password':
                        # user.set_password(v)
                        pass
                    else:
                        setattr(user, k, v)
                user.save()
                if phone:
                    user.phone = phone
                    user.save()
                CkanHandler.update_user(user)
            else:
                user = User.objects.create_user(**form.cleaned_user_data)
                user.is_active = True
                user.save()
                CkanHandler.add_user(user, form.cleaned_user_data['password'], state='active')
    except (ValidationError, CkanBaseError) as e:
        raise GenericException(details=e.__str__())

    return user


class UserShow(APIView):

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        ]

    def get(self, request, username):
        data = handler_get_request(request)
        for item in data:
            if item['username'] == username:
                return JsonResponse(item, safe=True)
        raise Http404()

    def put(self, request, username):
        """Mettre à jour un utilisateur."""
        request.PUT, request._files = parse_request(request)
        if not request.user.is_admin:
            raise Http404()
        try:
            handle_pust_request(request, username=username)
        except Http404:
            raise Http404()
        except GenericException as e:
            return JsonResponse({'error': e.details}, status=400)
        return HttpResponse(status=204)


class UserList(APIView):

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        ]

    def get(self, request):
        data = handler_get_request(request)
        return JsonResponse(data, safe=False)

    def post(self, request):
        """Créer un utilisateur."""
        if not request.user.is_admin:
            raise Http404()
        try:
            user = handle_pust_request(request)
        except Http404:
            raise Http404()
        except GenericException as e:
            return JsonResponse({'error': e.details}, status=400)
        response = HttpResponse(status=201)
        response['Content-Location'] = user.profile.api_location
        return response
