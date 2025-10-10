from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from unfold.decorators import display

from .models import PhoneField


class ShowPhoneMixin:
    """A mixing to show a Phone field."""

    @display(description=_("Phone number"))
    def show_phone(self, obj):
        """Renders an object's telephone link."""
        formatted = PhoneField.format(obj.phone_number)
        return mark_safe(f'<a href="tel:{obj.phone_number}">{formatted}</a>')
