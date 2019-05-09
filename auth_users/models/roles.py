from django.conf import settings
from django.db import models
from django.utils import timezone


class UserOrganisationRoles(models.Model):
    class Meta(object):
        abstract = True
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


class LiaisonsReferents(UserOrganisationRoles):

    class Meta(object):
        verbose_name = "Statut de référent"
        verbose_name_plural = "Statuts de référent"
        unique_together = (
            ('user', 'organisation'),
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


class LiaisonsContributeurs(UserOrganisationRoles):

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


class Role(models.Model):
    REFERENT = 1
    CONTRIBUTOR = 2
    ADMIN_CRIGE = 3
    ROLE_CHOICES = (
        (REFERENT, 'referent'),
        (CONTRIBUTOR, 'contributeur'),
        (ADMIN_CRIGE, 'gestionnaire CRIGE'),
    )

    id = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, primary_key=True)
    organisations = models.ManyToManyField(to='idgo_admin.Organisation',)

    def __str__(self):
        return self.get_id_display()
