from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group as GroupBase
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """A model manager for the User model without a username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Creates and saves a User given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Creates and saves a regular User."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Creates and saves a SuperUser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        for field in ('is_staff', 'is_superuser'):
            if extra_fields.get(field) is not True:
                raise ValueError(f"Superuser must have {field}=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """An extension of the default User model."""

    # We don't need a username in this project.
    username = None
    # Email is the new username now, so it must be required and unique.
    email = models.EmailField(_('email address'), unique=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Must not include USERNAME_FIELD.

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email


class Group(GroupBase):
    """A proxy Group model created just to be included in admin site."""

    class Meta:
        proxy = True
        verbose_name = _('group')
        verbose_name_plural = _('groups')
