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

import os
import json
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command

from idgo_admin.models import Organisation
# from idgo_admin.models import Dataset
# from idgo_admin.models import Resource
from idgo_admin.models import AccountActions
# from idgo_admin.models import AsyncExtractorTask
# from idgo_admin.models import BaseMaps
# from idgo_admin.models import Category
from idgo_admin.models import Commune
from idgo_admin.models import Dataset
# from idgo_admin.models import DataType
# from idgo_admin.models import ExtractorSupportedFormat
# from idgo_admin.models import Granularity
from idgo_admin.models import Jurisdiction
from idgo_admin.models import JurisdictionCommune
# from idgo_admin.models import Keywords
# from idgo_admin.models import Layer
# from idgo_admin.models import License
from idgo_admin.models import LiaisonsContributeurs
from idgo_admin.models import LiaisonsReferents
# from idgo_admin.models import Mail
# from idgo_admin.models import Organisation
# from idgo_admin.models import OrganisationType
# from idgo_admin.models import RemoteCkan
# from idgo_admin.models import RemoteCkanDataset
# from idgo_admin.models import RemoteCsw
# from idgo_admin.models import RemoteCswDataset
# from idgo_admin.models import Resource
from idgo_admin.models import ResourceFormats
# from idgo_admin.models import Support
from idgo_admin.models import SupportedCrs
# from idgo_admin.models import Task

User = get_user_model()
logger = logging.getLogger('django')


def update_progress(desc, prog, tot):
    logger.info("{desc} - {prog}/{tot}".format(
        desc=desc, prog=prog + 1, tot=tot
    ))


class Command(BaseCommand):

    help = "Transfert données stock vers nouvelle instance"

    def add_arguments(self, parser):
        parser.add_argument(
            '-src', '--source',
            action='store',
            dest='source',
            help="Indique le chemin du dossier data. ",
        )

    def load_me(self, data_dir, batch):
        for fixture in batch:
            path = os.path.join(data_dir, fixture)
            call_command('loaddata', path, verbosity=2)
            logger.info("{} done".format(fixture))

    def load_user_profile(self, data_dir):
        call_command('loaddata', os.path.join(data_dir, 'user.json'), verbosity=0)
        with open(os.path.join(data_dir, 'profile.json')) as json_file:
            fixtures = json.load(json_file)
            for idx, data in enumerate(fixtures):
                fields = data.get('fields')
                try:
                    usr = User.objects.get(pk=fields.get('user'))
                except Exception:
                    logger.exception('Erreur ajout données de profil')
                else:
                    usr.phone = fields.get('phone')
                    usr.is_active = fields.get('is_active')
                    usr.is_admin = fields.get('is_admin')
                    try:
                        usr.organisation = Organisation.objects.get(pk=fields.get('organisation'))
                    except Exception:
                        pass
                    usr.phone = fields.get('phone')
                    usr.membership = fields.get('membership')
                    usr.crige_membership = fields.get('crige_membership')
                    usr.sftp_password = fields.get('sftp_password')
                    usr.profile_old_id = data.get('pk')
                    usr.user_old_id = fields.get('user')
                    usr.save()
                update_progress(
                    'User profiled {}'.format(
                        data.get('pk')), idx, len(fixtures))


    def load_accountactions(self, data_dir):
        with open(os.path.join(data_dir, 'accountactions.json')) as json_file:
            fixtures = json.load(json_file)
            for idx, data in enumerate(fixtures):
                fields = data.get('fields')
                profile = fields.pop('profile', None)
                fields['user'] = User.objects.get(profile_old_id=profile)
                if fields.get('organisation'):
                    fields['organisation'] = Organisation.objects.get(pk=fields.get('organisation'))
                AccountActions.objects.update_or_create(
                    pk=data.get('pk'), defaults=fields)
                update_progress(
                    'AccountActions {}'.format(
                        data.get('pk')), idx, len(fixtures))

    def load_juridiction_commune(self, data_dir):
        with open(os.path.join(data_dir, 'jurisdictioncommune.json')) as json_file:
            fixtures = json.load(json_file)
            for idx, data in enumerate(fixtures):
                fields = data.get('fields')
                if fields.get('created_by') is not None:
                    fields['created_by'] = User.objects.get(profile_old_id=fields.get('created_by'))
                fields['jurisdiction'] = Jurisdiction.objects.get(pk=fields.get('jurisdiction'))
                fields['commune'] = Commune.objects.get(pk=fields.get('commune'))

                JurisdictionCommune.objects.update_or_create(
                    pk=data.get('pk'), defaults=fields)
                update_progress(
                    'JurisdictionCommune {}'.format(
                        data.get('pk')), idx, len(fixtures))

    def load_liaisons_referents(self, data_dir):
        with open(os.path.join(data_dir, 'liaisonsreferents.json')) as json_file:
            fixtures = json.load(json_file)
            for idx, data in enumerate(fixtures):
                fields = data.get('fields')
                prf = fields.pop('profile', None)
                fields['user'] = User.objects.get(profile_old_id=prf)
                fields['organisation'] = Organisation.objects.get(pk=fields.get('organisation'))
                LiaisonsReferents.objects.update_or_create(
                    pk=data.get('pk'), defaults=fields)
                update_progress(
                    'LiaisonsReferents {}'.format(
                        data.get('pk')), idx, len(fixtures))

    def load_liaisons_contributeurs(self, data_dir):
        with open(os.path.join(data_dir, 'liaisonscontributeurs.json')) as json_file:
            fixtures = json.load(json_file)
            for idx, data in enumerate(fixtures):
                fields = data.get('fields')
                prf = fields.pop('profile', None)
                fields['user'] = User.objects.get(profile_old_id=prf)
                fields['organisation'] = Organisation.objects.get(pk=fields.get('organisation'))
                LiaisonsContributeurs.objects.update_or_create(
                    pk=data.get('pk'), defaults=fields)
                update_progress(
                    'LiaisonsContributeurs {}'.format(
                        data.get('pk')), idx, len(fixtures))

    def load_resource(self, data_dir):
        logger.info('start load resource')
        with open(os.path.join(data_dir, 'resource.json')) as json_file:
            fixtures = json.load(json_file)
            for data in fixtures:
                fields = data.get('fields')
                profiles = fields.pop('profiles_allowed', [])
                orgas = fields.pop('organisations_allowed', [])
                fields['format_type'] = ResourceFormats.objects.get(pk=fields.get('format_type'))
                fields['dataset'] = Dataset.objects.get(pk=fields.get('dataset'))
                fields['crs'] = SupportedCrs.objects.get(pk=fields.get('crs'))

                # Desactivé le temps de voir si possible a faire en sql
                # instance, _ = Resource.objects.update_or_create(
                #     pk=data.get('pk'), defaults=fields)
                # instance.profiles_allowed.set(profiles)
                # instance.organisations_allowed.set(orgas)

    def handle(self, *args, **options):
        source = options.get('source')

        if not source or not os.path.exists(source):
            logger.error(
                'Veuillez indiquer le chemin source avec le paramètre -src')
            return
        data_dir = source[:-1] if source.endswith('/') else source

        """
        user.json a été modifié: remplacment de 'auth.user' par 'auth_users.user'
        """
        # On charge les donnée user-profile
        # self.load_user_profile(data_dir)

        # On charge le premier lot
        batch = [
            'gdpr.json',  # modifé idgo_admin.gdpr par auth_users.gdpr
            'gdpruser.json',  # modifé idgo_admin.gdpruser par auth_users.gdpruser
            'site.json',
            # 'basemaps.json',  # vide lors des pretest
            'license.json',
            'category.json',
            'commune.json',
            'organisationtype.json',
            'jurisdiction.json',
            'organisation.json',  # Necessite Jurisdiction
            'support.json',
            'granularity.json',
            'datatype.json',
            'dataset.json',  # Necessite Organisation + Granurality + DataType
            'extractorsupportedformat.json',
            'resourceformats.json',
            'supportedcrs.json',
        ]
        self.load_me(data_dir, batch)

        # On charge des données qui doivent etre reatribué au bon user
        # Operations gourmande en temps

        # On a besoin au prealable que User et Jurisdiction soient en place
        self.load_juridiction_commune(data_dir)

        # On a besoin au préalable que User et Organisation soient en place
        self.load_liaisons_referents(data_dir)
        self.load_liaisons_contributeurs(data_dir)

        # On a besoin au préalable que User et Organisation soient en place
        self.load_accountactions(data_dir)

        # Désactivé car: Les synchro au save() sont complexes,
        # a voir si on passe pas par une requete de dump sql
        # On a besoin au prealable que User, ResourceFormat,
        # Organisation et Dataset et SupportedCrs soient en place
        # self.load_resource(data_dir)

        # On charge le dernier lot
        batch2 = [
            # 'layer.json',  # necessite Resource en place
            'mail.json',
            # 'data/asyncextractortask.json',  # vide lors des pre-test
            'remoteckan.json',
            'remoteckandataset.json',
            'mappingcategory.json',
            'mappinglicence.json',
            'remotecsw.json',
            'remotecswdataset.json',
            # 'task.json',  #vide lors des pre-test
            'tag.json',
        ]

        self.load_me(data_dir, batch2)
