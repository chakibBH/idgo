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
from idgo_admin.ckan_module import CkanManagerHandler
from idgo_admin.models import Category


class Command(BaseCommand):

    help = 'Synchroniser les catégories CKAN avec IDGO.'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.ckan = CkanManagerHandler()

    def handle(self, *args, **options):
        for category in Category.objects.all():
            if self.ckan.is_group_exists(category.slug):
                category.ckan_id = self.ckan.get_group(category.slug)['id']
                category.save()
                self.stdout.write("'{0}' updated".format(category.slug))
