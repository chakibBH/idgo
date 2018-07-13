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


import ast
from django.conf import settings
from functools import reduce
from functools import wraps
from idgo_admin.datagis import get_description
from idgo_admin.exceptions import GenericException
from idgo_admin.utils import Singleton
from idgo_admin.utils import slugify
from requests import request
import timeout_decorator
from urllib.parse import urljoin


MRA = settings.MRA
MRA_TIMEOUT = MRA.get('TIMEOUT', 3600)
MRA_DATAGIS_USER = MRA['DATAGIS_DB_USER']
DB_SETTINGS = settings.DATABASES[settings.DATAGIS_DB]


def timeout(fun):
    t = MRA_TIMEOUT  # in seconds

    @timeout_decorator.timeout(t, use_signals=False)
    def return_with_timeout(fun, args=tuple(), kwargs=dict()):
        return fun(*args, **kwargs)

    @wraps(fun)
    def wrapper(*args, **kwargs):
        return return_with_timeout(fun, args=args, kwargs=kwargs)

    return wrapper


class MRASyncingError(GenericException):
    def __init__(self, *args, **kwargs):
        for item in self.args:
            try:
                m = ast.literal_eval(item)
            except Exception:
                continue
            if isinstance(m, dict):
                kwargs.update(**m)
            # else: TODO
        super().__init__(*args, **kwargs)


class MRANotFoundError(GenericException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MRAConflictError(GenericException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MRATimeoutError(MRASyncingError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MRAExceptionsHandler(object):

    def __init__(self, ignore=None):
        self.ignore = ignore or []

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                if self.is_ignored(e):
                    return f(*args, **kwargs)
                if e.__class__.__qualname__ == 'HTTPError':
                    if e.response.status_code == 404:
                        raise MRANotFoundError
                    if e.response.status_code == 409:
                        raise MRAConflictError
                if isinstance(e, timeout_decorator.TimeoutError):
                    raise MRATimeoutError
                if self.is_ignored(e):
                    return f(*args, **kwargs)
                print(e)
                raise MRASyncingError(e.__str__())
        return wrapper

    def is_ignored(self, exception):
        return type(exception) in self.ignore


class MRAClient(object):

    def __init__(self, url, username=None, password=None):
        self.base_url = url
        self.auth = (username and password) and (username, password)

    @timeout
    def _req(self, method, url, extension='json', **kwargs):
        kwargs.setdefault('allow_redirects', True)
        kwargs.setdefault('headers', {'content-type': 'application/json; charset=utf-8'})
        # TODO pretty:
        url = '{0}.{1}'.format(
            reduce(urljoin, (self.base_url,) + tuple(m + '/' for m in url))[:-1],
            extension)
        r = request(method, url, auth=self.auth, **kwargs)
        r.raise_for_status()
        if r.status_code == 200:
            if extension == 'json':
                try:
                    return r.json()
                except Exception as e:
                    if e.__class__.__qualname__ == 'JSONDecodeError':
                        return {}
                    raise e
            return r.text

    def get(self, *url, **kwargs):
        return self._req('get', url, **kwargs)

    def post(self, *url, **kwargs):
        return self._req('post', url, **kwargs)

    def put(self, *url, **kwargs):
        return self._req('put', url, **kwargs)

    def delete(self, *url, **kwargs):
        return self._req('delete', url, **kwargs)


class MRAHandler(metaclass=Singleton):

    def __init__(self, *args, **kwargs):
        self.remote = MRAClient(
            MRA['URL'], username=MRA['USERNAME'], password=MRA['PASSWORD'])

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def get_workspace(self, ws_name):
        return self.remote.get('workspaces', ws_name)

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def del_workspace(self, ws_name):
        self.remote.delete('workspaces', ws_name)

    @MRAExceptionsHandler()
    def create_workspace(self, ws_name):
        json = {
            'workspace': {
                'name': ws_name}}

        self.remote.post('workspaces', json=json)

        return self.get_workspace(ws_name)

    def get_or_create_workspace(self, ws_name):
        try:
            return self.get_workspace(ws_name)
        except MRANotFoundError:
            pass
        return self.create_workspace(ws_name)

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def get_datastore(self, ws_name, ds_name):
        return self.remote.get('workspaces', ws_name,
                               'datastores', ds_name)

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def del_datastore(self, ws_name, ds_name):
        self.remote.delete('workspaces', ws_name,
                           'datastores', ds_name)

    @MRAExceptionsHandler()
    def create_datastore(self, ws_name, ds_name):
        json = {
            'dataStore': {
                'name': ds_name,
                'connectionParameters': {
                    'host': DB_SETTINGS['HOST'],
                    'user': MRA_DATAGIS_USER,
                    'database': DB_SETTINGS['NAME'],
                    'dbtype': DB_SETTINGS['ENGINE'].split('.')[-1],
                    'password': DB_SETTINGS['PASSWORD'],
                    'port': DB_SETTINGS['PORT']}}}

        self.remote.post('workspaces', ws_name,
                         'datastores', json=json)

        return self.get_datastore(ws_name, ds_name)

    def get_or_create_datastore(self, ws_name, ds_name):
        try:
            return self.get_datastore(ws_name, ds_name)
        except MRANotFoundError:
            pass
        return self.create_datastore(ws_name, ds_name)

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def get_featuretype(self, ws_name, ds_name, ft_name):
        return self.remote.get('workspaces', ws_name,
                               'datastores', ds_name,
                               'featuretypes', ft_name)

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def del_featuretype(self, ws_name, ds_name, ft_name):
        self.remote.delete('workspaces', ws_name,
                           'datastores', ds_name,
                           'featuretypes', ft_name)

    @MRAExceptionsHandler()
    def create_featuretype(self, ws_name, ds_name, ft_name, enabled=True):
        json = {
            'featureType': {
                'name': ft_name,
                'title': ft_name,
                'abstract': ft_name,
                'enabled': enabled}}

        self.remote.post('workspaces', ws_name,
                         'datastores', ds_name,
                         'featuretypes', json=json)

        return self.get_featuretype(ws_name, ds_name, ft_name)

    def get_or_create_featuretype(self, ws_name, ds_name, ft_name, enabled=True):
        try:
            return self.get_featuretype(ws_name, ds_name, ft_name)
        except MRANotFoundError:
            pass
        return self.create_featuretype(ws_name, ds_name, ft_name, enabled=enabled)

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def get_style(self, s_name, as_sld=True):
        return self.remote.get('styles', s_name, extension='sld',
                               headers={'content-type': 'application/vnd.ogc.sld+xml; charset=utf-8'})

    @MRAExceptionsHandler()
    def create_style(self, s_name, data):
        return self.remote.post(
            'styles', extension='sld', params={'name': s_name}, data=data,
            headers={'content-type': 'application/vnd.ogc.sld+xml; charset=utf-8'})

    @MRAExceptionsHandler()
    def update_style(self, s_name, data):
        return self.remote.put(
            'styles', s_name, extension='sld', data=data,
            headers={'content-type': 'application/vnd.ogc.sld+xml; charset=utf-8'})

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def create_or_update_style(self, s_name, data):
        try:
            self.update_style(s_name, data)
        except MRANotFoundError:
            self.create_style(s_name, data)

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def get_layer(self, l_name):
        return self.remote.get('layers', l_name)['layer']

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def update_layer_defaultstyle(self, l_name, s_name):
        json = {'layer': self.get_layer(l_name)}
        json['layer']['defaultStyle']['name'] = s_name
        json['layer']['defaultStyle']['href'] = '{0}styles/{1}.json'.format(MRA['URL'], s_name)
        return self.remote.put('layers', l_name, json=json)

    @MRAExceptionsHandler(ignore=[MRANotFoundError])
    def del_layer(self, l_name):
        self.remote.delete('layers', l_name)

    @MRAExceptionsHandler()
    def update_layer(self, l_name, data):
        return self.remote.put('layers', l_name, json={'layer': data})

    @MRAExceptionsHandler()
    def enable_layer(self, l_name):
        self.update_layer(l_name, {'enabled': True})

    @MRAExceptionsHandler()
    def disable_layer(self, l_name):
        self.update_layer(l_name, {'enabled': False})

    @MRAExceptionsHandler()
    def enable_wms(self, ws_name=None):
        self.remote.put('services', 'workspaces', ws_name, 'wms', 'settings',
                        json={'wms': {'enabled': True}})

    @MRAExceptionsHandler()
    def disable_wms(self, ws_name=None):
        self.remote.put('services', 'workspaces', ws_name, 'wms', 'settings',
                        json={'wms': {'enabled': False}})

    @MRAExceptionsHandler()
    def enable_wfs(self, ws_name=None):
        self.remote.put('services', 'workspaces', ws_name, 'wfs', 'settings',
                        json={'wfs': {'enabled': True}})

    @MRAExceptionsHandler()
    def disable_wfs(self, ws_name=None):
        self.remote.put('services', 'workspaces', ws_name, 'wfs', 'settings',
                        json={'wfs': {'enabled': False}})

    def publish_layers_resource(self, resource):

        ws_name = resource.dataset.organisation.ckan_slug
        self.get_or_create_workspace(ws_name)

        ds_name = 'public'
        self.get_or_create_datastore(ws_name, ds_name)

        enabled = resource.ogc_services
        for datagis_id in resource.datagis_id:
            self.get_or_create_featuretype(
                ws_name, ds_name, datagis_id, enabled=enabled)

        self.enable_wms(ws_name=ws_name)
        self.enable_wfs(ws_name=ws_name)

    @MRAExceptionsHandler()
    def get_fonts(self, ws_name=None):
        return self.remote.get('fonts')['fonts']

MRAHandler = MRAHandler()