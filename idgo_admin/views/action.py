from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from idgo_admin.exceptions import ExceptionsHandler
from idgo_admin.models import Dataset
from idgo_admin.shortcuts import get_object_or_404_extended
from idgo_admin.shortcuts import GetProfile


decorators = [csrf_exempt, login_required(login_url=settings.LOGIN_URL)]


@method_decorator(decorators, name='dispatch')
class ActionsManager(View):

    @GetProfile()
    @ExceptionsHandler(ignore=[Http404])
    def get(self, request, *args, **kwargs):
        user = kwargs.get('user')
        # profile = kwargs.get('profile')

        dataset_id = request.GET.get('id', None)
        publish = request.GET.get('publish', None)

        if dataset_id and publish.lower() == 'toggle':
            ds = get_object_or_404_extended(
                Dataset, user, include={'id': dataset_id})

            # TODO(cbenhabib): author=profile in Dataset model
            # instance = get_object_or_404_extended(
            #     Dataset, profile, include={'id': dataset_id})

            ds.published = not ds.published
            message = (
                'Le jeu de données <strong>{0}</strong> '
                'est maintenant en accès <strong>{1}</strong>.'
                ).format(ds.name, ds.published and 'public' or 'privé')
            status = 200
            ds.save()

        return render(request, 'idgo_admin/response.html',
                      context={'message': message}, status=status)
