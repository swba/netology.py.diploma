import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from rest_framework.test import APIClient

from .utils import generate_password, user_make_and_login


@pytest.fixture
def api_client() -> APIClient:
    """Returns API client for testing."""
    return APIClient()

@pytest.fixture(scope='session')
def user_make_factory():
    """Returns a factory for users with passwords."""
    user_prepare_factory = model_prepare_factory(get_user_model())
    def factory(*args, **kwargs):
        def set_password_and_save(user):
            password = generate_password()
            user.set_password(password)
            user.save()
            user._password = password
        users = user_prepare_factory(*args, **kwargs)
        if type(users) is list:
            for u in users:
                set_password_and_save(u)
        else:
            set_password_and_save(users)
        return users
    return factory

@pytest.fixture
def api_client_auth(api_client, user_make_factory) -> APIClient:
    """Returns API client with access credentials."""
    response = user_make_and_login(api_client, user_make_factory)
    api_client.credentials(
        HTTP_AUTHORIZATION='Bearer ' + response.data['access']
    )
    api_client._user = response._user
    return api_client

@pytest.fixture(scope='session')
def user_prepare_factory():
    """Returns a factory to prepare User instances."""
    return model_prepare_factory(get_user_model())

def model_make_factory(model):
    """Returns a factory to make model instances."""
    def factory(*args, **kwargs):
        return baker.make(
            model,
            *args,
            _fill_optional=True,
            **kwargs
        )
    return factory

def model_prepare_factory(model):
    """Returns a factory to prepare model instances."""
    def factory(*args, **kwargs):
        return baker.prepare(
            model,
            *args,
            _fill_optional=True,
            **kwargs
        )
    return factory
