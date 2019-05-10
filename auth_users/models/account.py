from django.apps import apps
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
import requests
from auth_users.managers import UserManager


FTP_SERVICE_URL = settings.FTP_SERVICE_URL


class User(AbstractUser):

    email = models.EmailField(_('email address'), unique=True)

    phone = models.CharField(
        verbose_name="Téléphone",
        max_length=10,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        verbose_name="Validation suite à confirmation mail par utilisateur",
        default=False,
    )

    membership = models.BooleanField(
        verbose_name="Utilisateur rattaché à une organisation",
        default=False,
    )

    crige_membership = models.BooleanField(
        verbose_name="Utilisateur affilié au CRIGE",
        default=False,
    )

    is_admin = models.BooleanField(
        verbose_name="Administrateur métier",
        default=False,
    )

    sftp_password = models.CharField(
        verbose_name="Mot de passe sFTP",
        max_length=10,
        blank=True,
        null=True,
    )

    # A utiliser lors de la migrations pour retablir les liens avec les instances liés
    # A supprimer apres intégration
    user_old_id = models.PositiveIntegerField(
        verbose_name="Ancien id user",
        blank=True,
        null=True
    )

    profile_old_id = models.PositiveIntegerField(
        verbose_name="Ancien id profil",
        blank=True,
        null=True
    )

    organisation = models.ForeignKey(
        to='idgo_admin.Organisation',
        verbose_name="Organisation d'appartenance",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    referents = models.ManyToManyField(
        to='idgo_admin.Organisation',
        through='idgo_admin.LiaisonsReferents',
        related_name='profile_referents',
        verbose_name="Organisations dont l'utilisateur est réferent",
    )

    contributions = models.ManyToManyField(
        to='idgo_admin.Organisation',
        through='idgo_admin.LiaisonsContributeurs',
        related_name='profile_contributions',
        verbose_name="Organisations dont l'utilisateur est contributeur",
    )

    roles = models.ManyToManyField(to='idgo_admin.Role')

    # Objects Managers
    objects = UserManager()

    class Meta(object):
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils des utilisateurs"

    def __str__(self):
        return str(self.email)

    # Propriétés
    # ==========

    @property
    def is_agree_with_terms(self):
        Gdpr = apps.get_model(app_label='auth_users', model_name='Gdpr')
        GdprUser = apps.get_model(app_label='auth_users', model_name='GdprUser')
        try:
            GdprUser.objects.get(user=self, gdpr=Gdpr.objects.latest('issue_date'))
        except (GdprUser.DoesNotExist, Gdpr.DoesNotExist):
            return False
        else:
            return True

    @property
    def is_referent(self):
        kwargs = {'user': self, 'validated_on__isnull': False}
        LiaisonsReferents = apps.get_model(
            app_label='idgo_admin', model_name='LiaisonsReferents')
        return LiaisonsReferents.objects.filter(**kwargs).exists()

    @property
    def referent_for(self):
        LiaisonsReferents = apps.get_model(
            app_label='idgo_admin', model_name='LiaisonsReferents')
        return LiaisonsReferents.get_subordinated_organisations(user=self)

    @property
    def is_contributor(self):
        kwargs = {'user': self, 'validated_on__isnull': False}
        LiaisonsContributeurs = apps.get_model(
            app_label='idgo_admin', model_name='LiaisonsContributeurs')
        return LiaisonsContributeurs.objects.filter(**kwargs).exists()

    @property
    def contribute_for(self):
        LiaisonsContributeurs = apps.get_model(
            app_label='idgo_admin', model_name='LiaisonsContributeurs')
        return LiaisonsContributeurs.get_contribs(user=self)

    @property
    def is_crige_admin(self):
        return self.is_admin and self.crige_membership

    @property
    def is_ftp_account_exists(self):
        return self.sftp_password and True or False

    # Méthodes de classe
    # ==================

    @classmethod
    def get_crige_membership(cls):
        return User.objects.filter(is_active=True, crige_membership=True)

    # Autres méthodes
    # ===============

    def get_roles(self, organisation=None, dataset=None):
        LiaisonsReferents = apps.get_model(
            app_label='idgo_admin', model_name='LiaisonsReferents')
        if organisation:
            is_referent = LiaisonsReferents.objects.filter(
                user=self,
                organisation=organisation,
                validated_on__isnull=False).exists()
        else:
            is_referent = LiaisonsReferents.objects.filter(
                user=self,
                validated_on__isnull=False).exists()

        return {'is_admin': self.is_admin,
                'is_referent': is_referent,
                'is_editor': (self.user == dataset.editor) if dataset else False}

    def is_referent_for(self, organisation):
        kwargs = {
            'organisation': organisation,
            'user': self,
            'validated_on__isnull': False}
        LiaisonsReferents = apps.get_model(
            app_label='idgo_admin', model_name='LiaisonsReferents')
        return LiaisonsReferents.objects.filter(**kwargs).exists()

    # Actions sur le compte FTP

    def create_ftp_account(self):
        params = {'action': 'create', 'login': self.user.username}
        r = requests.get(FTP_SERVICE_URL, params=params)
        if r.status_code == 200:
            details = r.json()
            self.sftp_password = details.get('message')
            self.save()

    def delete_ftp_account(self):
        params = {'action': 'delete', 'login': self.user.username}
        r = requests.get(FTP_SERVICE_URL, params=params)
        if r.status_code == 200:
            self.sftp_password = None
            self.save()
