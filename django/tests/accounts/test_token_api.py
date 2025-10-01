# noinspection PyPackageRequirements
import pytest
from rest_framework.test import APIClient

from tests.utils import assert_response, get_token_url, user_make_and_login


@pytest.mark.django_db
def test_tokens_get__wrong_email(api_client: APIClient, user_make_factory):
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
def test_tokens_get__wrong_password(api_client: APIClient, user_make_factory):
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
def test_tokens_get(api_client: APIClient, user_make_factory):
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
