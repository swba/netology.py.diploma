from typing import Literal

# noinspection PyPackageRequirements
import pytest
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.shop.models import Seller
from tests.utils import get_seller_url, assert_response


def grant_permission(user: User, permission: Literal['add', 'change', 'delete']):
    """Grants given permission to the user."""
    p = Permission.objects.get(codename=f'{permission}_seller')
    user.user_permissions.add(p)

def serialize(seller: Seller):
    """Serializes a seller instance.

    We apply manual serialization instead of using SellerSerializer to
    be 100% sure endpoints return what we want to see.
    """
    return {
        'id': seller.id,
        'title': seller.title,
        'website_url': seller.website_url,
        'business_info': seller.business_info,
        'is_active': seller.is_active,
    }


@pytest.mark.django_db
def test_seller_add__anonymous(api_client: APIClient):
    """Test adding a seller (anonymous user)."""
    response = api_client.post(get_seller_url(), {})
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_seller_add__no_permission(api_client_auth: APIClient):
    """Test adding a seller (no permission)."""
    response = api_client_auth.post(get_seller_url(), {
        'title': 'Apple'
    })
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action.",
    })

@pytest.mark.django_db
def test_seller_add__no_data(api_client_auth: APIClient):
    """Test adding a seller (no data)."""
    # noinspection PyUnresolvedReferences
    grant_permission(api_client_auth._user, 'add')
    response = api_client_auth.post(get_seller_url(), {})
    assert_response(response, 400, {
        'title': ["This field is required."],
        'business_info': ["This field is required."],
    })

@pytest.mark.django_db
def test_seller_add(api_client_auth: APIClient):
    """Test adding a seller."""
    # noinspection PyUnresolvedReferences
    grant_permission(api_client_auth._user, 'add')
    data = {
        'title': "Apple",
        'website_url': "https://apple.com",
        'business_info': "A well-known hardware and software producer. Kind of.",
        'is_active': True,
    }
    response = api_client_auth.post(get_seller_url(), data)
    assert_response(response, 201, data | {
        'id': 1,
    })

@pytest.mark.django_db
def test_seller_list(api_client_auth: APIClient, seller_factory):
    """Test retrieving a list of sellers."""
    sellers = seller_factory(_quantity=10)
    response = api_client_auth.get(get_seller_url())
    assert_response(response, 200, [
        serialize(seller) for seller in sellers[::-1]
    ])

@pytest.mark.django_db
def test_seller_get__missing(api_client_auth: APIClient):
    """Test retrieving a missing seller details."""
    response = api_client_auth.get(get_seller_url(1))
    assert_response(response, 404, {
        'detail': "No Seller matches the given query."
    })

@pytest.mark.django_db
def test_seller_get(api_client_auth: APIClient, seller_factory):
    """Test retrieving a single seller details."""
    seller = seller_factory()
    response = api_client_auth.get(get_seller_url(seller.pk))
    assert_response(response, 200, serialize(seller))

@pytest.mark.django_db
def test_seller_edit__anonymous(api_client: APIClient, seller_factory):
    """Test updating a seller (anonymous user)."""
    seller = seller_factory()
    response = api_client.patch(get_seller_url(seller.pk), {
        'title': "New title",
    })
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_seller_edit__no_permission(api_client_auth: APIClient, seller_factory):
    """Test updating a seller (no permission)."""
    seller = seller_factory()
    response = api_client_auth.patch(get_seller_url(seller.pk), {
        'title': "New title",
    })
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action.",
    })

@pytest.mark.django_db
def test_seller_edit__not_owner(api_client_auth: APIClient, seller_factory, user_factory):
    """Test updating a seller (under another user)."""
    seller = seller_factory(user=user_factory())
    # noinspection PyUnresolvedReferences
    grant_permission(api_client_auth._user, 'change')
    response = api_client_auth.patch(get_seller_url(seller.pk), {
        'title': "New title",
    })
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action.",
    })

@pytest.mark.django_db
def test_seller_edit(api_client_auth: APIClient, seller_factory):
    """Test updating a seller (under another user)."""
    # noinspection PyUnresolvedReferences
    user = api_client_auth._user
    seller = seller_factory(user=user)
    grant_permission(user, 'change')
    response = api_client_auth.patch(get_seller_url(seller.pk), {
        'title': "New title",
    })
    assert_response(response, 200, serialize(seller) | {
        'title': "New title"
    })

@pytest.mark.django_db
def test_seller_delete__anonymous(api_client: APIClient, seller_factory):
    """Test deleting a seller (anonymous user)."""
    seller = seller_factory()
    response = api_client.delete(get_seller_url(seller.pk))
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_seller_delete__no_permission(api_client_auth: APIClient, seller_factory):
    """Test deleting a seller (no permission)."""
    seller = seller_factory()
    response = api_client_auth.delete(get_seller_url(seller.pk))
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action.",
    })

@pytest.mark.django_db
def test_seller_delete__not_owner(api_client_auth: APIClient, seller_factory, user_factory):
    """Test deleting a seller (under another user)."""
    seller = seller_factory(user=user_factory())
    # noinspection PyUnresolvedReferences
    grant_permission(api_client_auth._user, 'delete')
    response = api_client_auth.delete(get_seller_url(seller.pk))
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action.",
    })

@pytest.mark.django_db
def test_seller_delete(api_client_auth: APIClient, seller_factory):
    """Test deleting a seller (under another user)."""
    # noinspection PyUnresolvedReferences
    user = api_client_auth._user
    seller = seller_factory(user=user)

    # Ensure the seller is here.
    response = api_client_auth.get(get_seller_url(seller.pk))
    assert_response(response, 200, serialize(seller))

    # Delete it.
    grant_permission(user, 'delete')
    api_client_auth.delete(get_seller_url(seller.pk))

    # Ensure teh seller was deleted.
    response = api_client_auth.get(get_seller_url(seller.pk))
    assert_response(response, 404, {
        'detail': "No Seller matches the given query."
    })
