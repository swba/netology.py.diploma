from typing import Literal

import pytest
from django.urls import reverse

from apps.accounts.models import User
from tests.utils import assert_response, generate_password

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


@pytest.mark.django_db
def test_user_register__password_missing(api_client, user_prepare_factory):
    """Test user registration (missing password)."""
    response = api_client.post(get_user_url(), {
        'email': user_prepare_factory().email,
    })
    assert_response(response, 400, {
        'password': ["This field is required."]
    })

@pytest.mark.django_db
def test_user_register__email_missing(api_client):
    """Test user registration (missing email)."""
    response = api_client.post(get_user_url(), {
        'password': generate_password(),
    })
    assert_response(response, 400, {
        'email': ["This field is required."]
    })

@pytest.mark.django_db
def test_user_register__password_empty(api_client, user_prepare_factory):
    """Test user registration (empty password)."""
    response = api_client.post(get_user_url(), {
        'email': user_prepare_factory().email,
        'password': '',
    })
    assert_response(response, 400, {
        'password': ["This field may not be blank."]
    })

@pytest.mark.django_db
def test_user_register__password_simple(api_client, user_prepare_factory):
    """Test user registration (one-digit password)."""
    response = api_client.post(get_user_url(), {
        'email': user_prepare_factory().email,
        'password': '1',
    })
    assert_response(response, 400, {
        'password': [
            "This password is too short. It must contain at least 8 characters.",
            "This password is too common.",
            "This password is entirely numeric."
        ]
    })

@pytest.mark.django_db
def test_user_register__password_common_numeric(api_client, user_prepare_factory):
    """Test user registration (common numeric password)."""
    response = api_client.post(get_user_url(), {
        'email': user_prepare_factory().email,
        'password': '1234567890',
    })
    assert_response(response, 400, {
        'password': [
            "This password is too common.",
            "This password is entirely numeric."
        ]
    })

@pytest.mark.django_db
def test_user_register__password_common_alpha(api_client, user_prepare_factory):
    """Test user registration (common alpha password)."""
    response = api_client.post(get_user_url(), {
        'email': user_prepare_factory().email,
        'password': 'qwertyui',
    })
    assert_response(response, 400, {
        'password': [
            "This password is too common.",
        ]
    })

@pytest.mark.django_db
def test_user_register__password_similar_to_email(api_client):
    """Test user registration (password resembles email)."""
    response = api_client.post(get_user_url(), {
        'email': 'test@test.com',
        'password': 'Test1@test.com',
    })
    assert_response(response, 400, {
        'password': [
            "The password is too similar to the email address.",
        ]
    })

@pytest.mark.django_db
def test_user_register__bare_minimum(api_client, user_prepare_factory):
    """Test user registration (just email and password)."""
    user = user_prepare_factory()
    data = {
        'email': user.email,
    }
    password = generate_password()
    response = api_client.post(get_user_url(), data | {
        'password': password,
    })
    assert_response(response, 201, data | {
        'id': 1,
        'first_name': '',
        'last_name': ''
    })

@pytest.mark.django_db
def test_user_register(api_client, user_prepare_factory) -> User:
    """Test user registration (full data)."""
    user: User = user_prepare_factory()
    data = {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }
    password = generate_password()
    response = api_client.post(get_user_url(), data | {
        'password': password,
    })
    assert_response(response, 201, data | {
        'id': 1,
    })
    # Set raw password and return user instance as it's used in other
    # tests.
    user = User.objects.get(email=user.email)
    user.password = password
    return user

@pytest.mark.django_db
def test_user_register__exists(api_client, user_prepare_factory):
    """Test user registration (existing user)."""
    user = test_user_register(api_client, user_prepare_factory)
    response = api_client.post(get_user_url(), {
        'email': user.email,
        'password': generate_password(),
    })
    assert_response(response, 400, {
        'email': ["user with this email address already exists."]
    })

@pytest.mark.django_db
def test_user_login(api_client, user_prepare_factory) -> dict:
    """Test user login (obtain a pair of tokens)."""
    user = test_user_register(api_client, user_prepare_factory)
    response = api_client.post(get_token_url(), {
        'email': user.email,
        'password': user.password,
    })
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 2
    assert 'refresh' in json and 'access' in json
    # Return tokens as they are used in other tests.
    return json

@pytest.mark.django_db
def test_user_login__wrong_email(api_client, user_prepare_factory):
    """Test user login (incorrect email)."""
    user = test_user_register(api_client, user_prepare_factory)
    response = api_client.post(get_token_url(), {
        'email': user.email + 'y',
        'password': user.password,
    })
    assert_response(response, 401, {
        'detail': "No active account found with the given credentials"
    })

@pytest.mark.django_db
def test_user_login__wrong_password(api_client, user_prepare_factory):
    """Test user login (incorrect password)."""
    user = test_user_register(api_client, user_prepare_factory)
    response = api_client.post(get_token_url(), {
        'email': user.email,
        'password': 'OopsIdidItAgain',
    })
    assert_response(response, 401, {
        'detail': "No active account found with the given credentials"
    })

@pytest.mark.django_db
def test_user_token_verify(api_client, user_prepare_factory):
    """Test token verify."""
    tokens = test_user_login(api_client, user_prepare_factory)
    # Verify access token.
    response = api_client.post(get_token_url('verify'), {
        'token': tokens['access'],
    })
    assert response.status_code == 200
    # Verify refresh token.
    response = api_client.post(get_token_url('verify'), {
        'token': tokens['refresh'],
    })
    assert response.status_code == 200

@pytest.mark.django_db
def test_user_token_verify__wrong_token(api_client, user_prepare_factory):
    """Test token verify (wrong token)."""
    tokens = test_user_login(api_client, user_prepare_factory)
    # Verify incorrect access token.
    response = api_client.post(get_token_url('verify'), {
        'token': tokens['access'] + 'y',
    })
    assert response.status_code == 401
    # Verify incorrect refresh token.
    response = api_client.post(get_token_url('verify'), {
        'token': tokens['refresh'] + 'y',
    })
    assert response.status_code == 401

@pytest.mark.django_db
def test_user_token_refresh(api_client, user_prepare_factory):
    """Test token refresh."""
    tokens = test_user_login(api_client, user_prepare_factory)
    response = api_client.post(get_token_url('refresh'), {
        'refresh': tokens['refresh'],
    })
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 2
    assert 'access' in json

@pytest.mark.django_db
def test_user_token_refresh__wrong_token(api_client, user_prepare_factory):
    """Test token refresh (wrong refresh token)."""
    tokens = test_user_login(api_client, user_prepare_factory)
    response = api_client.post(get_token_url('refresh'), {
        'refresh': tokens['refresh'] + 'y',
    })
    assert_response(response, 401, {
        'detail': "Token is invalid",
        'code': 'token_not_valid'
    })
