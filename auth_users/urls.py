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
from django.conf.urls.static import static
from django.conf.urls import url
from auth_users.views.account import create_sftp_account
from auth_users.views.account import delete_account
from auth_users.views.account import delete_sftp_account
from auth_users.views.account import PasswordManager
from auth_users.views.account import ReferentAccountManager
from auth_users.views.account import SignUp
from auth_users.views.account import UpdateAccount
from auth_users.views.account import SignIn
from auth_users.views.account import SignOut
from auth_users.views.gdpr import GdprView

urlpatterns = [
    url('^create/?$', SignUp.as_view(), name='sign_up'),
    url('^update/?$', UpdateAccount.as_view(), name='update_account'),
    url('^delete/?$', delete_account, name='deleteAccount'),


    url('^cas/login/?$', SignIn.as_view(), name='signIn'),
    url('^cas/logout/?$', SignOut.as_view(), name='signOut'),
    url('^signin/?$', SignIn.as_view(), name='signIn'),
    url('^signout/?$', SignOut.as_view(), name='signOut'),

    url('^sftp/create/?$', create_sftp_account, name='create_sftp_account'),
    url('^sftp/delete/?$', delete_sftp_account, name='delete_sftp_account'),

    url('^terms/?$', GdprView.as_view(), name='terms_agreement'),
    url('^member/all/?$', ReferentAccountManager.as_view(), name='all_members'),

    url('^password/(?P<process>(forget))/?$', PasswordManager.as_view(), name='password_manager'),
    url('^password/(?P<process>(initiate|reset))/(?P<key>(.+))/?$', PasswordManager.as_view(), name='password_manager'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
