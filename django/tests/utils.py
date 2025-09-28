import secrets
import string
from typing import Literal

from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.accounts.models import User


def get_user_url(pk: int = None) -> str:
    """Returns user endpoint URL.

    If user ID (pk) is specified, URL of the user detail endpoint is
    returned; otherwise, URL of the user list endpoint is returned.

    Args:
        pk: (optional) User ID.

    Returns:
        Endpoint URL.
    """
    if pk:
        return reverse('api.accounts:user-detail', kwargs={'pk': pk})
    return reverse('api.accounts:user-list')

def get_token_url(action: Literal['refresh', 'verify'] | None = None) -> str:
    """Returns token endpoint URL.

    Args:
        action: (optional) Token action to use. If not set, then URL of
        the get token (user login) endpoint is returned.

    Returns:
        Endpoint URL.
    """
    if not action:
        action = 'obtain_pair'
    return reverse(f'api.accounts:token_{action}')

def assert_response(response: Response, status: int, json: dict):
    """Asserts API response.

    Args:
        response: API response.
        status: Expected HTTP status code.
        json: Expected JSON response.

    Returns:
        Response JSON.
    """
    assert response.status_code == status
    assert response.data == json

def generate_password() -> str:
    """Generates an eight-character alphanumeric password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(8))

def user_make_and_login(api_client: APIClient, user_make_factory) -> Response:
    """Makes and logs in a user."""
    user = user_make_factory()
    response = api_client.post(get_token_url(), {
        'email': user.email,
        'password': user._password,
    })
    response._user = user
    return response
