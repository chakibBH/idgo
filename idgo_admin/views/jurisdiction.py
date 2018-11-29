# Copyright (c) 2017-2018 Datasud.
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


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.serializers import serialize
from django.db import transaction
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
# from idgo_admin.exceptions import ExceptionsHandler
# from idgo_admin.exceptions import ProfileHttp404
from idgo_admin.exceptions import FakeError
from idgo_admin.forms.jurisdiction import JurisdictionForm as Form
from idgo_admin.models import BaseMaps
from idgo_admin.models import Commune
from idgo_admin.models import Jurisdiction
from idgo_admin.models import JurisdictionCommune
from idgo_admin.models.mail import send_mail_asking_for_jurisdiction_creation
from idgo_admin.models import Organisation
# from idgo_admin.shortcuts import on_profile_http404
from idgo_admin.shortcuts import render_with_info_profile
from idgo_admin.shortcuts import user_and_profile
from math import ceil


CKAN_URL = settings.CKAN_URL

decorators = [csrf_exempt, login_required(login_url=settings.LOGIN_URL)]


@login_required(login_url=settings.LOGIN_URL)
@csrf_exempt
def jurisdiction(request, *args, **kwargs):

    user, profile = user_and_profile(request)

    id = request.GET.get('id', None)
    if not id:
        raise Http404

    instance = get_object_or_404(Jurisdiction, code=id)

    return redirect(reverse('idgo_admin:jurisdiction_editor', kwargs={'code': instance.code}))


@login_required(login_url=settings.LOGIN_URL)
@csrf_exempt
def jurisdictions(request, *args, **kwargs):

    user, profile = user_and_profile(request)

    # Accès réservé aux administrateurs IDGO
    if not profile.is_admin:
        raise Http404

    jurisdictions = Jurisdiction.objects.all()

    # Gestion du tri
    order_by = request.GET.get('sortby', None)
    if order_by:
        jurisdictions = jurisdictions.order_by(order_by)

    # Gestion de la pagination
    page_number = int(request.GET.get('page', 1))
    items_per_page = int(request.GET.get('count', 10))
    number_of_pages = ceil(len(jurisdictions) / items_per_page)
    if number_of_pages < page_number:
        page_number = 1
    x = items_per_page * page_number - items_per_page
    y = x + items_per_page

    context = {
        'jurisdictions': jurisdictions[x:y],
        'Organisation': Organisation,
        'pagination': {
            'current': page_number,
            'total': number_of_pages},
        'total': len(jurisdictions)}

    return render_with_info_profile(
        request, 'idgo_admin/jurisdiction/jurisdictions.html', context=context)


@method_decorator(decorators, name='dispatch')
class JurisdictionView(View):

    template = 'idgo_admin/jurisdiction/edit.html'

    def get(self, request, code):
        user, profile = user_and_profile(request)

        if code not in ('for', 'new'):
            fake = None
            jurisdiction = get_object_or_404(Jurisdiction, code=code)
        else:
            fake = (code == 'for')
            jurisdiction = None
            code = None

        organisation_pk = request.GET.get('organisation')
        if organisation_pk:
            organisation = get_object_or_404(Organisation, pk=organisation_pk)
        else:
            organisation = None

        form = Form(instance=jurisdiction, include={'user': user})

        basemaps = BaseMaps.objects.all()
        communes = serialize(
            'geojson', Commune.objects.all().transform(srid=4326),
            geometry_field='geom')

        context = {
            'basemaps': basemaps,
            'communes': communes,
            'fake': fake,
            'form': form,
            'instance': jurisdiction,
            'organisation': organisation}

        return render_with_info_profile(request, self.template, context=context)

    def post(self, request, code):

        user, profile = user_and_profile(request)

        if code not in ('for', 'new'):
            fake = None
            jurisdiction = get_object_or_404(Jurisdiction, code=code)
        else:
            fake = (code == 'for')
            jurisdiction = None
            code = None

        organisation_pk = request.GET.get('organisation')
        if organisation_pk:
            organisation = get_object_or_404(Organisation, pk=organisation_pk)
        else:
            organisation = None

        form = Form(request.POST, instance=jurisdiction, include={'user': user})

        basemaps = BaseMaps.objects.all()
        communes = serialize(
            'geojson', Commune.objects.all().transform(srid=4326),
            geometry_field='geom')

        context = {
            'basemaps': basemaps,
            'communes': communes,
            'fake': fake,
            'form': form,
            'instance': jurisdiction,
            'organisation': organisation}

        if not form.is_valid():
            return render_with_info_profile(request, self.template, context=context)

        try:
            with transaction.atomic():
                if not code:
                    jurisdiction = Jurisdiction.objects.create(**dict(
                        (item, form.cleaned_data[item])
                        for item in form.Meta.property_fields))
                else:
                    for item in form.Meta.property_fields:
                        setattr(jurisdiction, item, form.cleaned_data[item])
                    jurisdiction.save(old=code)

                for instance in JurisdictionCommune.objects.filter(jurisdiction=jurisdiction):
                    if instance.commune not in form.cleaned_data['communes']:
                        instance.delete()
                for commune in form.cleaned_data['communes']:
                    kvp = {'jurisdiction': jurisdiction, 'commune': commune}
                    try:
                        JurisdictionCommune.objects.get(**kvp)
                    except JurisdictionCommune.DoesNotExist:
                        kvp['created_by'] = profile
                        JurisdictionCommune.objects.create(**kvp)
                if fake:
                    url = '{}?organisation={}'.format(
                        request.build_absolute_uri(reverse(
                            'idgo_admin:jurisdiction_editor', kwargs={'code': 'new'})),
                        organisation.pk)

                    send_mail_asking_for_jurisdiction_creation(user, jurisdiction, organisation, url)
                    raise FakeError('Force atomic to roll back.')

        except ValidationError as e:
            messages.error(request, ' '.join(e))
        except FakeError as e:
            messages.success(request, (
                'Votre demande de création de territoire '
                'de compétence a été envoyée aux administrateurs.'))
        else:
            messages.success(request, (
                'Le territoire de compétence a été '
                '{} avec succès.').format(code and 'mis à jour' or 'créé'))

        if 'save' in request.POST:
            to = '{}#{}'.format(
                reverse('idgo_admin:jurisdictions'), jurisdiction.code)
        else:
            to = reverse(
                'idgo_admin:jurisdiction_editor',
                kwargs={'code': jurisdiction.code})

        if fake:
            # S'il s'agit d'une simple demande on revient
            # toujours sur la liste des organisations
            to = reverse('idgo_admin:all_organizations')

        return HttpResponseRedirect(to)

    def delete(self, request, code, *args, **kwargs):

        if code == 'new':
            raise Http404

        user, profile = user_and_profile(request)
        jurisdiction = get_object_or_404(Jurisdiction, code=code)

        try:
            with transaction.atomic():
                jurisdiction.delete()
        except Exception as e:
            messages.error(request, e.__str__())
        else:
            messages.success(request, 'Le territoire de compétence a été supprimé avec succès.')

        return HttpResponse(status=200)
