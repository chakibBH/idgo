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
from django.db import transaction
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from idgo_admin.ckan_module import CkanHandler as ckan
from idgo_admin.ckan_module import CkanUserHandler as ckan_me
from idgo_admin.exceptions import CkanBaseError
from idgo_admin.exceptions import ExceptionsHandler
from idgo_admin.exceptions import ProfileHttp404
from idgo_admin.forms.resource import ResourceForm as Form
from idgo_admin.models import Dataset
from idgo_admin.models.mail import send_resource_creation_mail
from idgo_admin.models.mail import send_resource_delete_mail
from idgo_admin.models.mail import send_resource_update_mail
from idgo_admin.models import Resource
from idgo_admin.shortcuts import get_object_or_404_extended
from idgo_admin.shortcuts import on_profile_http404
from idgo_admin.shortcuts import render_with_info_profile
from idgo_admin.shortcuts import user_and_profile
import json


CKAN_URL = settings.CKAN_URL


decorators = [csrf_exempt, login_required(login_url=settings.LOGIN_URL)]


@login_required(login_url=settings.LOGIN_URL)
@csrf_exempt
def resource(request, dataset_id=None, *args, **kwargs):
    user, profile = user_and_profile(request)

    id = request.GET.get('id', request.GET.get('ckan_id'))
    if not id:
        raise Http404

    kvp = {}
    try:
        id = int(id)
    except ValueError:
        kvp['ckan_id'] = id
    else:
        kvp['id'] = id
    finally:
        instance = get_object_or_404(Resource, **kvp)

    # TODO:
    # return redirect(reverse('idgo_admin:resource_editor', kwargs={
    #     'dataset_id': instance.dataset.id, 'resource_id': instance.id}))
    return redirect(
        '{}?id={}'.format(
            reverse(
                'idgo_admin:resource', kwargs={'dataset_id': instance.dataset.id}),
            instance.id))


@method_decorator(decorators, name='dispatch')
class ResourceManager(View):

    template = 'idgo_admin/dataset/resource/resource.html'
    namespace = 'idgo_admin:resource'

    def get_context(self, form, profile, dataset, resource):

        if resource:
            mode = (
                resource.up_file and 'up_file' or
                resource.dl_url and 'dl_url' or
                resource.referenced_url and 'referenced_url' or
                resource.ftp_file and 'ftp_file'
                ) or None
        elif form:
            mode = (
                form.files.get('up_file') and 'up_file' or
                form.data.get('dl_url') and 'dl_url' or
                form.data.get('referenced_url') and 'referenced_url' or
                form.data.get('ftp_file') and 'ftp_file'
                ) or None

        return {
            'dataset': dataset,
            'form': form,
            'mode': mode,
            'resource': resource}

    @ExceptionsHandler(actions={ProfileHttp404: on_profile_http404})
    def get(self, request, dataset_id=None, *args, **kwargs):

        user, profile = user_and_profile(request)

        dataset = get_object_or_404_extended(
            Dataset, user, include={'id': dataset_id})

        # Redirect to layer
        _resource = request.GET.get('resource')
        _layer = request.GET.get('layer')
        if _resource and _layer:
            return redirect(
                reverse('idgo_admin:layer_editor', kwargs={
                    'dataset_id': dataset.id,
                    'resource_id': _resource,
                    'layer_id': _layer}))

        id = request.GET.get('id')
        instance = id and get_object_or_404_extended(
            Resource, user, include={'id': id, 'dataset_id': dataset.id}) or None

        form = Form(instance=instance, user=user)

        context = self.get_context(form, profile, dataset, instance)

        return render_with_info_profile(request, self.template, context)

    @ExceptionsHandler(ignore=[Http404], actions={ProfileHttp404: on_profile_http404})
    @transaction.atomic
    def post(self, request, dataset_id=None, *args, **kwargs):

        # Vider systèmatiquement les messages
        storage = messages.get_messages(request)
        storage.used = True

        user, profile = user_and_profile(request)

        dataset = get_object_or_404_extended(
            Dataset, user, include={'id': dataset_id})

        id = request.POST.get('id', request.GET.get('id'))
        instance = id and get_object_or_404_extended(
            Resource, user, include={'id': id, 'dataset': dataset}) or None

        form = Form(
            request.POST, request.FILES,
            instance=instance, dataset=dataset, user=user)

        context = self.get_context(form, profile, dataset, instance)

        ajax = 'ajax' in request.POST
        save_and_continue = 'continue' in request.POST

        if not form.is_valid():
            if ajax:
                error = dict([(k, [str(m) for m in v]) for k, v in form.errors.items()])
                msg = 'Veuillez corriger le formulaire.'
                if '__all__' in error:
                    error['__all__'].prepend(msg)
                else:
                    error['__all__'] = [msg]
                return JsonResponse(json.dumps({'error': error}), safe=False)
            return render_with_info_profile(request, self.template, context)

        try:
            with transaction.atomic():
                instance = form.handle_me(request, dataset, id=id)
        except ValidationError as e:
            if e.code == 'crs':
                form.add_error(e.code, '')
                form.add_error('__all__', e.message)
            elif e.code == 'encoding':
                form.add_error(e.code, '')
                form.add_error('__all__', e.message)
            else:
                form.add_error(e.code, e.message)
            messages.error(request, ' '.join(e))
            error = dict(
                [(k, [str(m) for m in v]) for k, v in form.errors.items()])
        except CkanBaseError as e:
            error = {'__all__': [e.__str__()]}
            form.add_error('__all__', e.__str__())
            messages.error(request, e.__str__())
        else:
            if id:
                send_resource_update_mail(user, instance)
            else:
                send_resource_creation_mail(user, instance)

            dataset_href = reverse(
                self.namespace, kwargs={'dataset_id': dataset_id})
            messages.success(request, (
                'La ressource a été {0} avec succès. Souhaitez-vous '
                '<a href="{1}">ajouter une nouvelle ressource</a> ? ou bien '
                '<a href="{2}/dataset/{3}/resource/{4}" target="_blank">'
                'voir la ressource dans CKAN</a> ?').format(
                id and 'mise à jour' or 'créée', dataset_href,
                CKAN_URL, dataset.ckan_slug, instance.ckan_id))

            if ajax:
                response = HttpResponse(status=201)  # Ugly hack
                if save_and_continue:
                    href = '{0}?id={1}'.format(dataset_href, instance.id)
                else:
                    href = '{0}?id={1}#resources/{2}'.format(
                        reverse('idgo_admin:dataset'), dataset_id, instance.id)
                response['Content-Location'] = href
                return response
            else:
                if save_and_continue:
                    return HttpResponseRedirect(
                        '{0}?id={1}'.format(dataset_href, instance.id))

                return HttpResponseRedirect('{0}?id={1}#resources/{2}'.format(
                    reverse('idgo_admin:dataset'), dataset_id, instance.id))

        if ajax:
            form._errors = None
            return JsonResponse(json.dumps({'error': error}), safe=False)
        return render_with_info_profile(request, self.template, context)

    @ExceptionsHandler(ignore=[Http404], actions={ProfileHttp404: on_profile_http404})
    def delete(self, request, dataset_id=None, *args, **kwargs):

        user, profile = user_and_profile(request)

        dataset = get_object_or_404_extended(
            Dataset, user, include={'id': dataset_id})

        id = request.POST.get('id', request.GET.get('id'))
        if not id:
            raise Http404
        instance = get_object_or_404_extended(
            Resource, user, include={'id': id, 'dataset': dataset})

        ckan_id = str(instance.ckan_id)

        ckan_user = ckan_me(ckan.get_user(user.username)['apikey'])
        try:
            ckan_user.delete_resource(ckan_id)
        except CkanBaseError as e:
            status = 500
            messages.error(request, e.__str__())
        else:
            instance.delete()
            send_resource_delete_mail(user, instance)

            status = 200
            message = 'La ressource a été supprimée avec succès.'
            messages.success(request, message)
        finally:
            ckan_user.close()

        return HttpResponse(status=status)
