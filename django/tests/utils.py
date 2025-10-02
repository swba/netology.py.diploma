import random
import secrets
import string
from functools import cache
from typing import Literal

from django.db.models import Min, Max
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.shop.models import Product


def get_user_url(pk: int = None) -> str:
    """Returns user endpoint URL.

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

def get_category_url(pk=None):
    """Returns category endpoint URL.

    Args:
        pk: (optional) Category ID.

    Returns:
        Endpoint URL.
    """
    if pk:
        return reverse('api.shop:category-detail', kwargs={'pk': pk})
    return reverse('api.shop:category-list')

def get_product_url(pk=None):
    """Returns product endpoint URL.

    Args:
        pk: (optional) Product ID.

    Returns:
        Endpoint URL.
    """
    if pk:
        return reverse('api.shop:product-detail', kwargs={'pk': pk})
    return reverse('api.shop:product-list')

def get_cart_url(pk=None):
    """Returns cart endpoint URL.

    Args:
        pk: (optional) Cart line item ID.

    Returns:
        Endpoint URL.
    """
    if not pk:
        return reverse('api.shop:cartlineitem-list')
    elif pk == 'clear':
        return reverse('api.shop:cartlineitem-clear')
    else:
        return reverse('api.shop:cartlineitem-detail', kwargs={'pk': pk})

def get_shipping_address_url(pk=None):
    """Returns shipping address endpoint URL.

    Args:
        pk: (optional) Shipping address ID.

    Returns:
        Endpoint URL.
    """
    if pk:
        return reverse('api.shop:shippingaddress-detail', kwargs={'pk': pk})
    return reverse('api.shop:shippingaddress-list')

def get_order_url(pk=None):
    """Returns order endpoint URL.

    Args:
        pk: (optional) Order ID.

    Returns:
        Endpoint URL.
    """
    if pk:
        return reverse('api.shop:order-detail', kwargs={'pk': pk})
    return reverse('api.shop:order-list')

def assert_response(response: Response, status: int, json: dict|list):
    """Asserts API response.

    Args:
        response: API response.
        status: Expected HTTP status code.
        json: Expected JSON response.
    """
    assert response.status_code == status
    assert response.data == json

def generate_password() -> str:
    """Generates an eight-character alphanumeric password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))

def user_make_and_login(api_client: APIClient, user_make_factory) -> Response:
    """Makes and logs in a user."""
    user = user_make_factory()
    # noinspection PyProtectedMember
    response = api_client.post(get_token_url(), {
        'email': user.email,
        'password': user._password,
    })
    response._user = user
    return response

# noinspection PyShadowingNames
def get_random_substring(string: str, count: int) -> str:
    """Returns a random substring of a string."""
    index = random.randint(0, len(string) - count)
    return string[index:index + count]

def get_random_price_range() -> tuple[int, int]:
    """Returns random product price range."""
    min_price, max_price = get_product_price_range()
    p1 = random.randint(min_price, max_price)
    p2 = random.randint(min_price, max_price)
    return min(p1, p2), max(p1, p2)

@cache
def get_product_price_range() -> tuple[int, int]:
    """Returns product price range."""
    return Product.objects.aggregate(Min('price'), Max('price')).values()
