from django.utils.text import slugify as django_slugify
from unidecode import unidecode


def slugify(text: str):
    """Slugifies Unicore text."""
    return django_slugify(unidecode(text))
