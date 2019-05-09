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
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from idgo_admin.models import AccountActions
from idgo_admin.models import LiaisonsContributeurs
from idgo_admin.models import LiaisonsReferents
from idgo_admin.models import Resource


CKAN_URL = settings.CKAN_URL
CRIGE_URL = settings.CRIGE_URL
WORDPRESS_URL = settings.WORDPRESS_URL
READTHEDOC_URL = settings.READTHEDOC_URL
DEFAULT_CONTACT_EMAIL = settings.DEFAULT_CONTACT_EMAIL
DEFAULT_PLATFORM_NAME = settings.DEFAULT_PLATFORM_NAME
FTP_URL = settings.FTP_URL


@login_required(login_url=settings.LOGIN_URL)
def render_with_info_profile(
        request, template_name, context=None,
        content_type=None, status=None, using=None, *args, **kwargs):

    user = request.user

    if not context:
        context = {}

    organisation = (user.organisation and user.membership) and user.organisation

    try:
        action = AccountActions.objects.get(
            action='confirm_rattachement', user=user, closed__isnull=True)
    except Exception:
        awaiting_member_status = []
    else:
        awaiting_member_status = action.organisation \
            and [action.organisation.id, action.organisation.legal_name]

    contributor = [
        [c.id, c.legal_name] for c
        in LiaisonsContributeurs.get_contribs(user=user)]

    awaiting_contributor_status = [
        [c.id, c.legal_name] for c
        in LiaisonsContributeurs.get_pending(user=user)]

    referent = [
        [c.id, c.legal_name] for c
        in LiaisonsReferents.get_subordinated_organisations(user=user)]

    awaiting_referent_statut = [
        [c.id, c.legal_name] for c
        in LiaisonsReferents.get_pending(user=user)]

    context.update({
        'contact_email': DEFAULT_CONTACT_EMAIL,
        'platform_name': DEFAULT_PLATFORM_NAME,
        'ftp_url': FTP_URL,
        'doc_url': READTHEDOC_URL,
        'wordpress_url': WORDPRESS_URL,
        'crige_url': CRIGE_URL,
        'ckan_url': CKAN_URL,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_crige': user.crige_membership,
        'is_membership': user.membership,
        'is_referent': user.get_roles()['is_referent'],
        'is_contributor': len(contributor) > 0,
        'is_admin': user.is_admin,
        'organisation': organisation,
        'awaiting_member_status': awaiting_member_status,
        'contributor': contributor,
        'awaiting_contributor_status': awaiting_contributor_status,
        'referent': referent,
        'awaiting_referent_statut': awaiting_referent_statut,
        })

    return render(request, template_name, context=context,
                  content_type=content_type, status=status, using=using)


def get_object_or_404_extended(MyModel, user, include):
    res = None
    instance = get_object_or_404(MyModel, **include)

    i_am_resource = (MyModel.__name__ == Resource.__name__)
    dataset = instance.dataset if i_am_resource else instance

    is_referent = dataset.is_referent(user)
    is_contributor = dataset.is_contributor(user)
    is_editor = dataset.editor == user

    if user.is_admin or is_referent:
        res = instance
    if is_contributor and is_editor:
        res = instance

    if not res:
        raise PermissionDenied
    return res
