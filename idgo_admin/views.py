from .forms.dataset import DatasetForm
from .forms.dataset import ResourceForm
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from idgo_admin.models import Dataset
from idgo_admin.models import Resource
import json
from profiles.ckan_module import CkanHandler as ckan
from profiles.ckan_module import CkanUserHandler as ckan_me


decorators = [csrf_exempt, login_required(login_url=settings.LOGIN_URL)]


def render_on_error(request):
    dform = DatasetForm(include={'user': request.user})
    return render(request, 'idgo_admin/dataset.html', {'dform': dform})


def render_an_critical_error(request):
    message = ("Une erreur critique s'est produite "
               'lors de la suppression du jeu de donnée.')

    return JsonResponse(data={'message': message}, status=400)


@method_decorator(decorators, name='dispatch')
class DatasetManager(View):

    def get(self, request):
        user = request.user

        id = request.GET.get('id') or None
        if id:
            dataset = get_object_or_404(Dataset, id=id, editor=user)

            resources = [
                (o.pk,
                 o.name,
                 o.created_on.isoformat() if o.created_on else None,
                 o.last_update.isoformat() if o.last_update else None,
                 o.access.name) for o in Resource.objects.filter(dataset=dataset)]

            return render(request, 'idgo_admin/dataset.html',
                          {'first_name': user.first_name,
                           'last_name': user.last_name,
                           'dataset_name': dataset.name,
                           'dataset_id': dataset.id,
                           'resources': json.dumps(resources),
                           'dform': DatasetForm(
                               instance=dataset,
                               include={'user': request.user})})

        return render(request, 'idgo_admin/dataset.html',
                      {'first_name': user.first_name,
                       'last_name': user.last_name,
                       'dataset_name': 'Nouveau',
                       'resources': '[]',
                       'dform': DatasetForm(include={'user': user})})

    def post(self, request):
        user = request.user
        id = request.POST.get('id', request.GET.get('id')) or None
        if id:
            dataset = get_object_or_404(Dataset, id=id, editor=user)
            resources = [
                (o.pk,
                 o.name,
                 o.created_on.isoformat() if o.created_on else None,
                 o.last_update.isoformat() if o.last_update else None,
                 o.acces) for o in Resource.objects.filter(dataset=dataset)]

            dform = DatasetForm(instance=dataset,
                                data=request.POST,
                                include={'user': user})

            if not dform.is_valid() or not request.user.is_authenticated:
                return render(request, 'idgo_admin/dataset.html',
                              {'first_name': user.first_name,
                               'last_name': user.last_name,
                               'dataset_name': dataset.name,
                               'dataset_id': dataset.id,
                               'resources': json.dumps(resources),
                               'dform': DatasetForm(instance=dataset,
                                                    include={'user': user})})

            try:
                dform.handle_me(request, id)
            except Exception as e:
                message = ("L'erreur suivante est survenue : "
                           '<strong>{0}</strong>.').format(str(e))
            else:
                message = 'Le jeu de données a été mis à jour avec succès.'

            return render(request, 'profiles/information.html',
                          {'message': message}, status=200)
        else:
            dform = DatasetForm(
                data=request.POST, include={'user': request.user})
            if dform.is_valid() and request.user.is_authenticated:
                try:
                    dform.handle_me(request, id=request.GET.get('id'))
                except Exception as e:
                    message = ("L'erreur suivante est survenue : "
                               '<strong>{0}</strong>.').format(str(e))
                else:
                    message = 'Le jeu de données a été créé avec succès.'

                return render(request, 'profiles/information.html',
                              {'message': message}, status=200)

        return render_on_error(request)

    def delete(self, request):

        id = request.POST.get('id', request.GET.get('id')) or None
        if not id:
            return render_an_critical_error(request)

        dataset = get_object_or_404(Dataset, id=id, editor=request.user)
        name = dataset.name

        ckan_user = ckan_me(ckan.get_user(request.user.username)['apikey'])
        try:
            ckan_user.delete_dataset(str(dataset.ckan_id))
            ckan.purge_dataset(str(dataset.ckan_id))
        except Exception:
            dataset.delete()
            message = ('Le jeu de données <strong>{0}</strong> '
                       'ne peut pas être supprimé.').format(name)
            status = 400
        else:
            dataset.delete()
            message = ('Le jeu de données <strong>{0}</strong> '
                       'a été supprimé avec succès.').format(name)
            status = 200

        ckan_user.close()

        return render(request, 'profiles/response.htm',
                      {'message': message}, status=status)


@method_decorator(decorators, name='dispatch')
class ResourceManager(View):

    def get(self, request, dataset_id):
        user = request.user
        id = request.GET.get('id') or None
        dataset = get_object_or_404(Dataset, id=dataset_id)
        if id:
            resource = get_object_or_404(Resource, id=id,
                                         dataset_id=dataset_id)
            return render(request, 'idgo_admin/resource.html',
                          {'first_name': user.first_name,
                           'last_name': user.last_name,
                           'dataset_name': dataset.name,
                           'dataset_id': dataset.id,
                           'resource_name': resource.name,
                           'rform': ResourceForm(instance=resource)})

        return render(request, 'idgo_admin/resource.html',
                      {'first_name': user.first_name,
                       'last_name': user.last_name,
                       'dataset_name': dataset.name,  # TODO
                       'dataset_id': dataset.id,  # TODO
                       'resource_name': 'Nouveau',
                       'rform': ResourceForm()})

    def post(self, request, dataset_id):
        user = request.user
        id = request.POST.get('id', request.GET.get('id')) or None
        dataset = get_object_or_404(Dataset, id=dataset_id)
        if id:
            resource = get_object_or_404(Resource, id=id,
                                         dataset_id=dataset_id)
            rform = ResourceForm(instance=resource, data=request.POST)
            if not rform.is_valid() or not request.user.is_authenticated:
                return render(request, 'idgo_admin/resource.html',
                              {'first_name': user.first_name,
                               'last_name': user.last_name,
                               'dataset_name': dataset.name,
                               'dataset_id': dataset.id,
                               'resource_name': resource.name,
                               'rform': Resource(instance=resource)})

            try:
                rform.handle_me(request, dataset, id)
            except Exception as e:
                message = ("L'erreur suivante est survenue : "
                           '<strong>{0}</strong>.').format(str(e))
            else:
                message = 'La ressource a été mise à jour avec succès.'

            return render(request, 'profiles/information.html',
                          {'message': message}, status=200)
        else:
            rform = ResourceForm(data=request.POST)
            if rform.is_valid() and request.user.is_authenticated:
                try:
                    rform.handle_me(request, dataset)
                except Exception as e:
                    message = ("L'erreur suivante est survenue : "
                               '<strong>{0}</strong>.').format(str(e))
                else:
                    message = 'La ressource a été créée avec succès.'

                return render(request, 'profiles/information.html',
                              {'message': message}, status=200)

        return render(request, 'idgo_admin/resource.html', {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'dataset_name': dataset.name,  # TODO
            'dataset_id': dataset.id,  # TODO
            'resource_name': 'Nouveau',
            'rform': rform})

    def delete(self, request, dataset_id):

        id = request.POST.get('id', request.GET.get('id')) or None
        if not id:
            return render_an_critical_error(request)

        resource = get_object_or_404(Resource, id=id, dataset_id=dataset_id)

        # ckan_user = ckan_me(ckan.get_user(request.user.username)['apikey'])
        try:
            # TODO: services CKAN
            # ckan_user.delete_resource(str(dataset.ckan_id))
            # ckan.purge_resource(str(dataset.ckan_id))
            pass
        except Exception:
            message = ('La ressource <strong>{0}</strong> '
                       'ne peut pas être supprimé.').format(resource.name)
            status = 400
        else:
            resource.delete()
            message = ('Le jeu de données <strong>{0}</strong> '
                       'a été supprimé avec succès.').format(resource.name)
            status = 200

        # ckan_user.close()

        return render(request, 'profiles/response.htm',
                      {'message': message}, status=status)
