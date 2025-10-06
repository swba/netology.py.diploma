import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group as GroupBase
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.base.models import LoggableModel

from .managers import UserManager


class User(LoggableModel, AbstractUser):
    """An extension of the default User model."""

    # We don't need a username in this project.
    username = None
    # Email is the new username now, so it must be required and unique.
    email = models.EmailField(_('email address'), unique=True)
    is_verified = models.BooleanField(
        blank=True,
        default=False,
        verbose_name=_('Email verified'),)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Must not include USERNAME_FIELD.

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email


class UserToken(models.Model):
    """Token to confirm user emails and restore passwords."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='token',
        verbose_name=_('User'))
    value = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('Token value'))
    expires_at = models.DateTimeField(
        verbose_name=_('Expiration time'))

    class Meta:
        verbose_name = _('User token')
        verbose_name_plural = _('User tokens')

    def __str__(self):
        return f"Token for {self.user}"

    def save(self, *args, **kwargs):
        # Generate token value on first saving.
        if not self.value:
            self.value = secrets.token_urlsafe(32)
            self.expires_at = timezone.now() + settings.USER_TOKEN_LIFETIME
        super().save(*args, **kwargs)


class Group(GroupBase):
    """A proxy Group model created just to be included in admin site."""

    class Meta:
        proxy = True
        verbose_name = _('group')
        verbose_name_plural = _('groups')
