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

import json
import logging
from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command

from idgo_admin.models import Organisation
# from idgo_admin.models import Dataset
# from idgo_admin.models import Resource
# from idgo_admin.models import AccountActions
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
# from idgo_admin.models import LiaisonsContributeurs
# from idgo_admin.models import LiaisonsReferents
# from idgo_admin.models import Mail
# from idgo_admin.models import Organisation
# from idgo_admin.models import OrganisationType
# from idgo_admin.models import RemoteCkan
# from idgo_admin.models import RemoteCkanDataset
# from idgo_admin.models import RemoteCsw
# from idgo_admin.models import RemoteCswDataset
from idgo_admin.models import Resource
from idgo_admin.models import ResourceFormats
# from idgo_admin.models import Support
from idgo_admin.models import SupportedCrs
# from idgo_admin.models import Task


STOCK = settings.DATABASES['stock']['NAME']
User = get_user_model()
logger = logging.getLogger('django')


class Grabber(object):

    def __init__(self, db, sql, *args, **kwargs):
        self.db = db
        self.sql = sql
        super().__init__(*args, **kwargs)

    def connect_n_fetch(self):

        with connections[self.db].cursor() as cursor:
            try:
                cursor.execute(self.sql)
                columns = [col[0] for col in cursor.description]
                io_data = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]
            except Exception:
                logger.exception("La requete: {0} sur {1} retourne une erreur".format(sql, db))
                return None
        return io_data

    def fetch_first_row(self):
        list_dict = self.connect_n_fetch()
        if not list_dict or not len(list_dict):
            return {}
        return list_dict[0]


class Command(BaseCommand):

    help = "Transfert données stock vers nouvelle instance"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load_me(self, datum):
        for fixture in datum:
            call_command('loaddata', fixture, verbosity=0)
            logger.info("{} done".format(fixture))

    def load_profiles_for_users(self):
        with open('data/profile.json') as json_file:

            profiles = json.load(json_file)

            for data in profiles:
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

    def load_juridiction_commune(self):
        with open('data/jurisdictioncommune.json') as jc_file:
            juriscoms = json.load(jc_file)
            for data in juriscoms:
                fields = data.get('fields')
                logger.info(fields)
                if fields.get('created_by') is not None:
                    fields['created_by'] = User.objects.get(profile_old_id=fields.get('created_by'))
                fields['jurisdiction'] = Jurisdiction.objects.get(pk=fields.get('jurisdiction'))
                fields['commune'] = Commune.objects.get(pk=fields.get('commune'))

                JurisdictionCommune.objects.update_or_create(
                    pk=data.get('pk'), defaults=fields)

    def load_resource(self):
        logger.info('start load resource')
        with open('data/resource.json') as res_file:
            res = json.load(res_file)
            for data in res:
                fields = data.get('fields')
                logger.info(fields)
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
        """
        data/user.json a été modifié: remplacment de 'auth.user' par 'auth_users.user'
        """
        # On charge les donnée user-profile
        # call_command('loaddata', 'data/user.json', verbosity=0)
        # self.load_profiles_for_users()

        # On charge le premier lot
        datum = [
            'data/gdpr.json',  # modifé idgo_admin.gdpr par auth_users.gdpr
            'data/gdpruser.json',  # modifé idgo_admin.gdpruser par auth_users.gdpruser
            'data/sites.json',
            # 'data/basemaps.json',  # vide lors des pretest
            'data/licence.json',
            'data/category.json',
            'data/commune.json',
            'data/organisationtype.json',
            'data/organisation.json',
            'data/support.json',
            'data/dataset.json',
            'data/datatype.json',
            'data/extractorsupportedformat.json',
            'data/granularity.json',
            'data/jurisdiction.json',
            'data/resourceformats.json',
            'data/supportedcrs.json',
        ]
        # self.load_me(datum)

        # On charge des données qui doivent etre reatribué au bon user
        # Operations gourmande en temps

        # On a besoin au prealable que User et Jurisdiction soient en place
        # self.load_juridiction_commune()

        # On a besoin au prealable que User, ResourceFormat,
        # Organisation et Dataset et SupportedCrs soient en place
        # Les synchro au save() sont complexes,
        # a voir si on passe pas par une requete de dump sql
        # self.load_resource()

        # On charge le dernier lot
        datum3 = [
            # 'data/layer.json',  # necessite Resource en place
            'data/mail.json',
            'data/remoteckan.json',
            'data/remoteckandataset.json',
            'data/mappingcategory.json',
            'data/mappinglicence.json',
            'data/remotecsw.json',
            'data/remotecswdataset.json',
            # 'data/task.json',  #vide lors des pre-test
            'data/tag.json',
        ]

        self.load_me(datum3)
