from django.contrib.auth.models import AbstractUser, Group as GroupBase
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.base.models import LoggableModel

from .managers import UserManager


class User(LoggableModel, AbstractUser):
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
