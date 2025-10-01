# noinspection PyPackageRequirements
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from tests.utils import assert_response, generate_password, get_user_url


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

@pytest.mark.django_db
def test_user_patch__anonymous(api_client: APIClient, user_make_factory):
    """Test user update (anonymous request)."""
    user = user_make_factory()
    data = UserSerializer(instance=user).data
    response = api_client.patch(get_user_url(user.pk), data)
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_user_patch__another_user(api_client_auth: APIClient, user_make_factory):
    """Test user update (as another user)."""
    user = user_make_factory()
    data = UserSerializer(instance=user).data
    response = api_client_auth.patch(get_user_url(user.pk), data)
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action."
    })

@pytest.mark.django_db
def test_user_patch(api_client_auth: APIClient):
    """Test user update."""
    # noinspection PyUnresolvedReferences
    user = api_client_auth._user
    data = {
        'first_name': 'Quentin',
        'last_name': 'Tarantino',
    }
    response = api_client_auth.patch(get_user_url(user.pk), data)
    assert_response(response, 200, UserSerializer(instance=user).data | data)
