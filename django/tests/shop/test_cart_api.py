import random

# noinspection PyPackageRequirements
import pytest
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.shop.models import Product, CartLineItem
from tests.utils import get_cart_url, assert_response


def assert_cart(response: Response, status: int, expected: list[tuple[Product, int]]):
    """Asserts cart response.

    Args:
        response: The response object.
        status: Response status to assert.
        expected: Expected cart content as a list of tuples of products
            and their quantities.
    """
    # Cart content received from the API.
    content_received = []
    for item in response.data:
        content_received.append((
            item['product']['id'],
            item['product']['title'],
            item['product']['slug'],
            item['quantity']
        ))
    content_received.sort()

    # Expected cart content.
    content_expected = []
    for product, quantity in expected:
        content_expected.append((
            product.pk,
            product.title,
            product.slug,
            quantity
        ))
    content_expected.sort()

    assert response.status_code == status
    assert content_received == content_expected

@pytest.mark.django_db
def test_cart_list__anonymous(api_client: APIClient):
    """Test cart view (anonymous user)."""
    response = api_client.get(get_cart_url())
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_cart_list__empty(api_client_auth: APIClient, catalog_factory):
    """Test empty cart."""
    catalog_factory(1, 1)

    response = api_client_auth.get(get_cart_url())
    assert_response(response, 200, [])

@pytest.mark.django_db
def test_cart_add__no_product(api_client_auth: APIClient):
    """Test adding products to the cart (no product)."""
    response = api_client_auth.post(get_cart_url(), {})
    assert_response(response, 400, {
        'product_id': ["This field is required."]
    })

@pytest.mark.django_db
def test_cart_add__no_quantity(api_client_auth: APIClient, catalog_factory):
    """Test adding products to the cart (no quantity)."""
    catalog_factory(2, 2)

    p = Product.objects.first()

    response = api_client_auth.post(get_cart_url(), {
        'product_id': p.pk
    })
    assert_cart(response, 201, [(p, 1)])

@pytest.mark.django_db
def test_cart_add__too_many(api_client_auth: APIClient, product_factory):
    """Test adding products to the cart (quantity is too large)."""
    product = product_factory()
    quantity = product.quantity
    url = get_cart_url()

    response = api_client_auth.post(url, {
        'product_id': product.pk,
        'quantity': quantity + 1
    })
    assert_response(response, 400, {
        'quantity': ["Quantity exceeds the stock."]
    })

@pytest.mark.django_db
def test_cart_add__multiple(api_client_auth: APIClient, catalog_factory):
    """Test adding products to the cart (multiple products)."""
    catalog_factory(2, 2)
    url = get_cart_url()

    p1 = Product.objects.first()
    p2 = Product.objects.last()

    api_client_auth.post(url, {
        'product_id': p1.pk
    })
    response = api_client_auth.post(url, {
        'product_id': p2.pk,
        'quantity': 6
    })
    assert_cart(response, 201, [(p1, 1), (p2, 6)])

@pytest.mark.django_db
def test_cart_add__repeat(api_client_auth: APIClient, catalog_factory):
    """Test adding products to the cart (the same product twice)."""
    catalog_factory(1, 1)
    url = get_cart_url()

    p = Product.objects.first()

    api_client_auth.post(url, {
        'product_id': p.pk
    })
    response = api_client_auth.post(url, {
        'product_id': p.pk,
        'quantity': 6
    })
    assert_response(response, 400, {
        'detail': "Product is already in the cart."
    })

@pytest.mark.django_db
def test_cart_add__several_users(api_client_auth: APIClient, catalog_factory,
        user_factory):
    """Test adding products to the cart (several users)."""
    catalog_factory(2, 4)
    url = get_cart_url()

    users = [user_factory(), user_factory()]
    cart1 = []

    # Add all products to 3 carts (via API to the first one).
    for i, p in enumerate(Product.objects.all()):
        q = random.randint(1, 10)
        if i % 3 == 2:
            api_client_auth.post(url, {
                'product_id': p.pk,
                'quantity': q
            })
            cart1.append((p, q))
        else:
            CartLineItem(user=users[i % 3], product=p, quantity=q).save()

    response = api_client_auth.get(url)
    assert_cart(response, 200, cart1)

def _prepare_cart_for_edit(api_client_auth: APIClient, catalog_factory):
    """Adds all products to the current user's cart."""
    catalog_factory(2, 2)
    create_url = get_cart_url()

    cart = {}

    # Add all products to the cart one by one.
    for p in Product.objects.all():
        q = random.randint(1, p.quantity)
        response = api_client_auth.post(create_url, {
            'product_id': p.pk,
            'quantity': q
        })
        cart[response.data[-1]['id']] = (p, q)
        assert_cart(response, 201, list(cart.values()))

    return cart

@pytest.mark.django_db
def test_cart_update__too_many(api_client_auth: APIClient,
        cart_line_item_factory):
    """Test updating products to the cart (quantity is too large)."""
    # noinspection PyUnresolvedReferences
    item = cart_line_item_factory(user=api_client_auth._user)

    response = api_client_auth.patch(get_cart_url(item.pk), {
        'quantity': item.product.quantity + 1
    })
    assert_response(response, 400, {
        'quantity': ["Quantity exceeds the stock."]
    })

@pytest.mark.django_db
def test_cart_update(api_client_auth: APIClient, catalog_factory):
    """Test updating products to the cart."""
    cart = _prepare_cart_for_edit(api_client_auth, catalog_factory)

    # Increase quantities of products in the cart one by one.
    for pk, (p, q) in cart.items():
        response = api_client_auth.patch(get_cart_url(pk), {
            'quantity': q + 1
        })
        cart[pk] = (p, q + 1)
        assert_cart(response, 200, list(cart.values()))

@pytest.mark.django_db
def test_cart_delete(api_client_auth: APIClient, catalog_factory):
    """Test deleting products in the cart."""
    cart = _prepare_cart_for_edit(api_client_auth, catalog_factory)

    # Delete products from the cart one by one.
    while cart:
        pk, _ = cart.popitem()
        response = api_client_auth.delete(get_cart_url(pk))
        assert_cart(response, 200, list(cart.values()))

@pytest.mark.django_db
def test_cart_clear(api_client_auth: APIClient, catalog_factory):
    """Test clearing the cart."""
    _prepare_cart_for_edit(api_client_auth, catalog_factory)

    response = api_client_auth.delete(get_cart_url('all'))
    assert_response(response, 200, [])
