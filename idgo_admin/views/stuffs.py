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


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from idgo_admin.models import License
import requests


OWS_PREVIEW_URL = settings.OWS_PREVIEW_URL

try:
    MAPSERV_TIMEOUT = settings.MAPSERV_TIMEOUT
except AttributeError:
    MAPSERV_TIMEOUT = 60


@method_decorator([csrf_exempt], name='dispatch')
class DisplayLicenses(View):

    def get(self, request):
        data = [{
            'domain_content': license.domain_content,
            'domain_data': license.domain_data,
            'domain_software': license.domain_software,
            'family': '',  # TODO?
            'id': license.ckan_id,  # license.license_id
            'maintainer': license.maintainer,
            'od_conformance': license.od_conformance,
            'osd_conformance': license.osd_conformance,
            'status': license.status,
            'title': license.title,
            'url': license.url} for license in License.objects.all()]
        return JsonResponse(data, safe=False)


@login_required(login_url=settings.LOGIN_URL)
@csrf_exempt
def ows_preview(request):

    r = requests.get(
        OWS_PREVIEW_URL, params=dict(request.GET), timeout=MAPSERV_TIMEOUT)
    r.raise_for_status()
    return HttpResponse(r.content, content_type=r.headers['Content-Type'])
