import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from rest_framework.test import APIClient

@pytest.fixture(scope='session')
def api_client():
    """Returns API client for testing."""
    return APIClient()

@pytest.fixture(scope='session')
def user_make_factory():
    """Returns a factory to make User instances."""
    return model_make_factory(get_user_model())

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
            **kwargs
        )
    return factory

def model_prepare_factory(model):
    """Returns a factory to prepare model instances."""
    def factory(*args, **kwargs):
        return baker.prepare(
            model,
            *args,
            **kwargs
        )
    return factory
