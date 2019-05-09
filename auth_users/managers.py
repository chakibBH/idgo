from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    is_staff:
        + Indique si cet utilisateur peut, accéder au site d’administration.
        + Indique que cet utilisateur est un gestionnaire métier.
    is_superuser:
        + Indique que cet utilisateur possède, toutes les permissions
          sans avoir besoin de les lui attribuer explicitement.
        + Indique que cet utilisateur est un administrateur avec droits étendus.
    """

    # Sérialiser UserManager dans les migrations
    # pour qu’ils soient disponibles lors des opérations RunPython
    use_in_migrations = True

    def _create_user(self, username, email, password, **kwargs):

        if not email:
            raise ValueError('Adresse email obligatoire')
        if not username:
            raise ValueError('Login obligatoire')

        user = self.model(username=username, email=email, **kwargs)
        email = self.normalize_email(email)
        user.email = email
        user.set_password(password)

        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **kwargs):

        kwargs.setdefault('is_staff', False)
        kwargs.setdefault('is_superuser', False)
        kwargs.setdefault('is_active', False)

        return self._create_user(username, email, password, **kwargs)

    def create_superuser(self, username, email, password, **kwargs):

        kwargs.setdefault('is_active', True)
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)

        # Un numero est requis
        # Pour éviter d'ajouter un champs tel_ à la command manage.py createsuperuser
        # On set un numéro par default
        kwargs.setdefault('first_name', username)
        kwargs.setdefault('last_name', username)

        if kwargs.get('is_staff') is False:
            raise ValueError('Superuser must have is_staff=True.')
        if kwargs.get('is_superuser') is False:
            raise ValueError('Superuser must have is_superuser=True.')
        if kwargs.get('is_active') is False:
            raise ValueError('Superuser must have is_active=True.')

        return self._create_user(username, email, password, **kwargs)
