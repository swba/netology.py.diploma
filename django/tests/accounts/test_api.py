import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from tests.utils import (
    assert_response,
    generate_password,
    get_user_url,
    get_token_url,
    user_make_and_login
)


@pytest.mark.django_db
def test_user_register__password_missing(api_client: APIClient, user_prepare_factory):
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
def test_user_register__password_empty(api_client: APIClient, user_prepare_factory):
    """Test user registration (empty password)."""
    response = api_client.post(get_user_url(), {
        'email': user_prepare_factory().email,
        'password': '',
    })
    assert_response(response, 400, {
        'password': ["This field may not be blank."]
    })

@pytest.mark.django_db
def test_user_register__password_simple(api_client: APIClient, user_prepare_factory):
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
def test_user_register__password_common_numeric(api_client: APIClient, user_prepare_factory):
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
def test_user_register__password_common_alpha(api_client: APIClient, user_prepare_factory):
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
def test_user_register__password_similar_to_email(api_client: APIClient):
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
def test_user_register__bare_minimum(api_client: APIClient, user_prepare_factory):
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
def test_user_register(api_client: APIClient, user_prepare_factory):
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

@pytest.mark.django_db
def test_user_register__exists(api_client: APIClient, user_make_factory):
    """Test user registration (existing user)."""
    user = user_make_factory()
    response = api_client.post(get_user_url(), {
        'email': user.email,
        'password': generate_password(),
    })
    assert_response(response, 400, {
        'email': ["user with this email address already exists."]
    })

@pytest.mark.django_db
def test_user_login__wrong_email(api_client: APIClient, user_make_factory):
    """Test user login (incorrect email)."""
    user = user_make_factory()
    response = api_client.post(get_token_url(), {
        'email': user.email + 'y',
        'password': user._password,
    })
    assert_response(response, 401, {
        'detail': "No active account found with the given credentials"
    })

@pytest.mark.django_db
def test_user_login__wrong_password(api_client: APIClient, user_make_factory):
    """Test user login (incorrect password)."""
    user = user_make_factory()
    response = api_client.post(get_token_url(), {
        'email': user.email,
        'password': 'OopsIdidItAgain',
    })
    assert_response(response, 401, {
        'detail': "No active account found with the given credentials"
    })

@pytest.mark.django_db
def test_user_login(api_client: APIClient, user_make_factory):
    """Test user login (obtain a pair of tokens)."""
    response = user_make_and_login(api_client, user_make_factory)
    assert response.status_code == 200
    json = response.data
    assert len(json) == 2
    assert 'refresh' in json and 'access' in json

@pytest.mark.django_db
def test_token_verify__wrong_token(api_client: APIClient, user_make_factory):
    """Test token verify (wrong token)."""
    login_response = user_make_and_login(api_client, user_make_factory)
    # Verify incorrect access token.
    response = api_client.post(get_token_url('verify'), {
        'token': login_response.data['access'] + 'y',
    })
    assert response.status_code == 401
    # Verify incorrect refresh token.
    response = api_client.post(get_token_url('verify'), {
        'token': login_response.data['refresh'] + 'y',
    })
    assert response.status_code == 401

@pytest.mark.django_db
def test_token_verify(api_client: APIClient, user_make_factory):
    """Test token verify."""
    login_response = user_make_and_login(api_client, user_make_factory)
    # Verify access token.
    response = api_client.post(get_token_url('verify'), {
        'token': login_response.data['access'],
    })
    assert response.status_code == 200
    # Verify refresh token.
    response = api_client.post(get_token_url('verify'), {
        'token': login_response.data['refresh'],
    })
    assert response.status_code == 200

@pytest.mark.django_db
def test_token_refresh__wrong_token(api_client: APIClient, user_make_factory):
    """Test token refresh (wrong refresh token)."""
    login_response = user_make_and_login(api_client, user_make_factory)
    response = api_client.post(get_token_url('refresh'), {
        'refresh': login_response.data['refresh'] + 'y',
    })
    assert_response(response, 401, {
        'detail': "Token is invalid",
        'code': 'token_not_valid'
    })

@pytest.mark.django_db
def test_token_refresh(api_client: APIClient, user_make_factory):
    """Test token refresh."""
    login_response = user_make_and_login(api_client, user_make_factory)
    response = api_client.post(get_token_url('refresh'), {
        'refresh': login_response.data['refresh'],
    })
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 2
    assert 'access' in json

@pytest.mark.django_db
def test_user_get__anonymous(api_client: APIClient, user_make_factory):
    """Test user retrieve (anonymous request)."""
    user = user_make_factory()
    response = api_client.get(get_user_url(user.pk))
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_user_get__wrong_token(api_client: APIClient, user_make_factory):
    """Test user retrieve (incorrect access token)."""
    user = user_make_factory()
    api_client.credentials(HTTP_AUTHORIZATION='Bearer TralaleroTralala')
    response = api_client.get(get_user_url(user.pk))
    assert_response(response, 401, {
        'detail': "Given token not valid for any token type",
        'code': 'token_not_valid',
        'messages': [{
            'token_class': 'AccessToken',
            'token_type': 'access',
            'message': 'Token is invalid'
        }]
    })

@pytest.mark.django_db
def test_user_get__another_user(api_client_auth: APIClient, user_make_factory):
    """Test user retrieve (as another user)."""
    user = user_make_factory()
    response = api_client_auth.get(get_user_url(user.pk))
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action."
    })

@pytest.mark.django_db
def test_user_get(api_client_auth: APIClient):
    """Test user retrieve."""
    # noinspection PyUnresolvedReferences
    user = api_client_auth._user
    response = api_client_auth.get(get_user_url(user.pk))
    assert_response(response, 200, UserSerializer(instance=user).data)
