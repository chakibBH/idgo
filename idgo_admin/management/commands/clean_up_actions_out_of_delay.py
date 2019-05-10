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


from django.core.management.base import BaseCommand
from django.utils import timezone
from idgo_admin.models import LiaisonsContributeurs
from idgo_admin.models import LiaisonsReferents
from idgo_admin.models import AccountActions
import logging

logger = logging.getLogger('django')


class Command(BaseCommand):

    help = 'Nettoyer les demandes obsolètes.'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def n_days_ago(self, n):
        return timezone.now() - timezone.timedelta(days=n)

    def handle(self, *args, **options):

        del_org = []
        del_user = []
        old_actions = AccountActions.objects.filter(
            closed=None, created_on__lte=self.n_days_ago(2))

        for act in old_actions:
            pro_name, org_name = 'N/A', 'N/A'

            if act.user:
                pro_name = act.user.username
            if act.user.organisation:
                org_name = act.user.organisation.legal_name

            if act.action == 'confirm_rattachement':
                logger.info("clean_up_action Rattachement: {0}".format(pro_name))

            if act.action == 'confirm_mail':
                logger.info("clean_up_action User: {0}".format(pro_name))
                del_user.append(act.user)

            if act.action == 'confirm_new_organisation':
                logger.info("clean_up_action - New Orga: {0}".format(org_name))
                del_org.append(act.user.organisation)

            if act.action == 'confirm_contribution':
                liaison = LiaisonsContributeurs.objects.get(
                    user=act.user, organisation=act.organisation)
                logger.info("clean_up_action contribution: {0}-{1}".format(
                    pro_name, act.organisation.legal_name))
                liaison.delete()

            if act.action == 'confirm_referent':
                liaison = LiaisonsReferents.objects.get(
                    user=act.user, organisation=act.organisation)
                logger.info("clean_up_action referent: {0}-{1}".format(
                    pro_name, act.organisation.legal_name))
                liaison.delete()

            if act.action == 'reset_password':
                logger.info("clean_up_action Reset Password: {0}".format(act))

            act.delete()

        # Fait en second pour ne pas 'casser' la boucle précédente,
        # à cause des cascade_on_delete
        for u in del_user:
            logger.info("clean_up db - User: {0}".format(u.username))
            u.delete()

        for o in del_org:
            logger.info("clean_up db - New Orga: {0}".format(o.name))
            o.delete()
