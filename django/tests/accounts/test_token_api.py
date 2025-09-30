# noinspection PyPackageRequirements
import pytest
from rest_framework.test import APIClient

from apps.accounts.serializers import UserSerializer
from tests.utils import (
    assert_response,
    get_user_url,
    get_token_url,
    user_make_and_login
)


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
