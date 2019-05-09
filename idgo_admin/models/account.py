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


from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
import uuid
from idgo_admin.ckan_module import CkanHandler

User = get_user_model()

FTP_SERVICE_URL = settings.FTP_SERVICE_URL

try:
    ADMIN_USERNAME = settings.ADMIN_USERNAME
except AttributeError:
    ADMIN_USERNAME = None


# ==================
# Classes de liaison
# ==================


class LiaisonsReferents(models.Model):

    class Meta(object):
        verbose_name = "Statut de référent"
        verbose_name_plural = "Statuts de référent"
        unique_together = (
            ('user', 'organisation'),
            )

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        verbose_name='Profil utilisateur',
        on_delete=models.CASCADE,
        )

    organisation = models.ForeignKey(
        to='Organisation',
        verbose_name='Organisation',
        on_delete=models.CASCADE,
        )

    created_on = models.DateField(
        verbose_name="Date de la demande de statut de référent",
        auto_now_add=True,
        )

    validated_on = models.DateField(
        verbose_name="Date de la confirmation par un administrateur",
        blank=True,
        null=True,
        default=timezone.now,
        )

    def __str__(self):
        return '{full_name} ({username})--{organisation}'.format(
            full_name=self.user.get_full_name(),
            username=self.user.username,
            organisation=self.organisation.legal_name,
            )

    # Méthodes de classe
    # ==================

    @classmethod
    def get_subordinated_organisations(cls, user):

        # TODO: Sortir le rôle 'admin' (Attention à l'impact que cela peut avoir sur le code)
        if user.is_admin:
            Organisation = apps.get_model(app_label='idgo_admin', model_name='Organisation')
            return Organisation.objects.filter(is_active=True)

        kwargs = {'user': user, 'validated_on__isnull': False}
        return [e.organisation for e in LiaisonsReferents.objects.filter(**kwargs)]

    @classmethod
    def get_pending(cls, user):
        kwargs = {'user': user, 'validated_on': None}
        return [e.organisation for e in LiaisonsReferents.objects.filter(**kwargs)]


class LiaisonsContributeurs(models.Model):

    class Meta(object):
        verbose_name = "Statut de contributeur"
        verbose_name_plural = "Statuts de contributeur"
        unique_together = (
            ('user', 'organisation'),
            )

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        verbose_name="Profil utilisateur",
        on_delete=models.CASCADE,
        )

    organisation = models.ForeignKey(
        to='Organisation',
        verbose_name="Organisation",
        on_delete=models.CASCADE,
        )

    created_on = models.DateField(
        verbose_name="Date de la demande de statut de contributeur",
        auto_now_add=True,
        )

    validated_on = models.DateField(
        verbose_name="Date de la confirmation par un administrateur",
        blank=True,
        null=True,
        )

    def __str__(self):
        return '{full_name} ({username})--{organisation}'.format(
            full_name=self.user.get_full_name(),
            username=self.user.username,
            organisation=self.organisation.legal_name,
            )

    # Méthodes de classe
    # ==================

    @classmethod
    def get_contribs(cls, user):
        kwargs = {'user': user, 'validated_on__isnull': False}
        return [e.organisation for e in LiaisonsContributeurs.objects.filter(**kwargs)]

    @classmethod
    def get_contributors(cls, organisation):
        kwargs = {'organisation': organisation, 'validated_on__isnull': False}
        return [e.user for e in LiaisonsContributeurs.objects.filter(**kwargs)]

    @classmethod
    def get_pending(cls, user):
        kwargs = {'user': user, 'validated_on': None}
        return [e.organisation for e in LiaisonsContributeurs.objects.filter(**kwargs)]


# ===========================================
# Classe des actions de profile d'utilisateur
# ===========================================


class AccountActions(models.Model):

    key = models.UUIDField(
        verbose_name="Clé",
        editable=False,
        default=uuid.uuid4,
        )

    ACTION_CHOICES = (
        (
            'confirm_mail',
            "Confirmation de l'e-mail par l'utilisateur"
            ),
        (
            'confirm_new_organisation',
            "Confirmation par un administrateur de la création d'une organisation par l'utilisateur"
            ),
        (
            'confirm_rattachement',
            "Rattachement d'un utilisateur à une organisation par un administrateur"
            ),
        (
            'confirm_referent',
            "Confirmation du rôle de réferent d'une organisation pour un utilisateur par un administrateur"
            ),
        (
            'confirm_contribution',
            "Confirmation du rôle de contributeur d'une organisation pour un utilisateur par un administrateur"
            ),
        (
            'reset_password',
            "Réinitialisation du mot de passe"
            ),
        (
            'set_password_admin',
            "Initialisation du mot de passe suite à une inscription par un administrateur"
            ),
        )

    action = models.CharField(
        verbose_name="Action de gestion de profile",
        max_length=250,
        blank=True,
        null=True,
        choices=ACTION_CHOICES,
        default='confirm_mail',
        )

    created_on = models.DateTimeField(
        verbose_name="Date de création",
        blank=True,
        null=True,
        auto_now_add=True,
        )

    closed = models.DateTimeField(
        verbose_name="Date de validation",
        blank=True,
        null=True,
        )

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        )

    # Pour pouvoir reutiliser AccountActions pour demandes post-inscription
    organisation = models.ForeignKey(
        to='Organisation',
        verbose_name="Organisation",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        )

    def orga_name(self):
        return self.organisation and str(self.organisation.legal_name) or 'N/A'

    orga_name.short_description = "Nom de l'organisation concernée"

    def get_path(self):
        action = {
            'confirm_mail': (
                'confirmation_mail', {'key': self.key},
                ),
            'confirm_new_organisation': (
                'confirm_new_orga', {'key': self.key},
                ),
            'confirm_rattachement': (
                'confirm_rattachement', {'key': self.key},
                ),
            'confirm_referent': (
                'confirm_referent', {'key': self.key},
                ),
            'confirm_contribution': (
                'confirm_contribution', {'key': self.key},
                ),
            'reset_password': (
                'password_manager', {'key': self.key, 'process': 'reset'},
                ),
            'set_password_admin': (
                'password_manager', {'key': self.key, 'process': 'initiate'},
                ),
            }
        return reverse(
            'idgo_admin:{action}'.format(action=action[self.action][0]),
            kwargs=action[self.action][1])

    get_path.short_description = "Adresse de validation"


# Signaux
# =======


@receiver(pre_delete, sender=User)
def delete_ckan_user(sender, instance, **kwargs):
    CkanHandler.del_user(instance.username)


@receiver(post_save, sender=User)
def handle_crige_partner(sender, instance, **kwargs):
    groupname = 'crige-partner'

    username = instance.username
    if CkanHandler.is_user_exists(username):
        if instance.crige_membership:
            CkanHandler.add_user_to_partner_group(username, groupname)
        else:
            CkanHandler.del_user_from_partner_group(username, groupname)
