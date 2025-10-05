from django.conf import settings
from django.http import HttpRequest


# noinspection PyUnusedLocal
def django_settings(request: HttpRequest = None) -> dict:
    """Provides Django settings context.

    This context provides a limited set of settings for security
    reasons.
    """
    return {
        'SITE_NAME': settings.SITE_NAME,
    }
