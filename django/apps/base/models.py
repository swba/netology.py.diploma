from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class LoggableModel(models.Model):
    """Abstract model providing created_at and updated_at fields."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PhoneField(models.CharField):
    """A phone field with validation."""

    pattern = r'^\+[1-9]\d{10,12}$'

    def __init__(
            self,
            *args,
            max_length=14,
            default='',
            blank=True,
            help_text=_("Phone number in international format: +79995550022"),
            **kwargs
        ):
        super().__init__(*args, **kwargs)
        self.max_length = max_length
        self.default = default
        self.blank = blank
        self.help_text = help_text
        self.validators = [RegexValidator(self.pattern)]

    @staticmethod
    def format(value):
        if value and len(value) >= 12:
            return f"{value[:-10]} {value[-10:-7]} {value[-7:-4]}-{value[-4:]}"
        return value
