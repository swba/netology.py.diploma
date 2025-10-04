import random

# noinspection PyPackageRequirements
import pytest
# noinspection PyPackageRequirements
import rstr
from django.contrib.auth import get_user_model
# noinspection PyPackageRequirements
from model_bakery import baker
from rest_framework.test import APIClient

from apps.base.models import PhoneField
from apps.shop.models import (
    Category,
    Product,
    Seller,
    ShippingAddress,
    Order,
    CartLineItem,
    OrderLineItem
)

from .utils import generate_password, user_make_and_login


def generate_phone_number() -> str:
    """Generates a random phone number."""
    return rstr.xeger(PhoneField.pattern)


@pytest.fixture
def api_client() -> APIClient:
    """Returns API client for testing."""
    return APIClient()

@pytest.fixture(scope='session')
def user_factory():
    """Returns a factory for users with passwords."""
    def factory(*args, _save=True, **kwargs):
        user_factory = model_factory(get_user_model())
        users = user_factory(*args, _save=False, **kwargs)
        if _save:
            def set_password_and_save(user):
                password = generate_password()
                user.set_password(password)
                user.save()
                user._password = password
            if type(users) is list:
                for u in users:
                    set_password_and_save(u)
            else:
                set_password_and_save(users)
        return users
    return factory

@pytest.fixture
def api_client_auth(api_client, user_factory) -> APIClient:
    """Returns API client with access credentials."""
    response = user_make_and_login(api_client, user_factory)
    api_client.credentials(
        HTTP_AUTHORIZATION='Bearer ' + response.data['access']
    )
    # noinspection PyUnresolvedReferences,PyProtectedMember
    api_client._user = response._user
    return api_client

@pytest.fixture(scope='session')
def category_factory():
    """Returns a factory to make category instances."""
    return model_factory(Category)

@pytest.fixture(scope='session')
def product_factory(seller_factory):
    """Returns a factory to make product instances."""
    f = model_factory(Product)
    def factory(*args, **kwargs):
        # Default product quantity is zero, so ensure we have something
        # in the stock.
        if 'quantity' not in kwargs:
            kwargs['quantity'] = random.randint(100, 500)
        if 'seller' not in kwargs:
            kwargs['seller'] = seller_factory(is_active=True)
        return f(*args, **kwargs)
    return factory

@pytest.fixture(scope='session')
def catalog_factory(user_factory, seller_factory, category_factory, product_factory):
    """Returns a factory for catalog (categories with products).

    The factory being returned creates 5-10 sellers, 5-10 catalog
    categories and 5-10 products in every category associated with
    a random seller.
    """
    def factory(min_objects: int = 5, max_objects: int = 10):
        def add_products(category: Category):
            products = product_factory(
                seller=random.choice(sellers),
                _quantity=random.randint(min_objects, max_objects)
            )
            category.products.add(*products)
        sellers = seller_factory(
            user=user_factory(),
            is_active=True,
            _quantity=random.randint(min_objects, max_objects)
        )
        categories = category_factory(
            _quantity=random.randint(min_objects, max_objects)
        )
        if type(categories) is list:
            for cat in categories:
                add_products(cat)
        else:
            add_products(categories)
        return categories
    return factory

@pytest.fixture(scope='session')
def shipping_address_factory():
    """Returns a factory to make shipping address instances."""
    f = model_factory(ShippingAddress)
    # Create one more factory wrapper around a factory to add a random
    # pone number to shipping address(es) being generated. Approach
    # with `baker.generators.add()` doesn't work because PhoneNumber
    # field has default value which is always used by model_bakery
    # unless is overwritten manually.
    def factory(*args, **kwargs):
        _kwargs = {**kwargs}
        if 'phone_number' not in _kwargs:
            _kwargs['phone_number'] = generate_phone_number()
        return f(*args, **_kwargs)
    return factory

@pytest.fixture(scope='session')
def order_factory(cart_line_item_factory):
    """Returns a factory to make order instances."""
    f = model_factory(Order)
    line_item_factory = model_factory(OrderLineItem)
    def factory(*args, _save=True, **kwargs):
        if 'line_items' not in kwargs:
            kwargs['line_items'] = line_item_factory(_quantity=3)
        return f(*args, _save=True, **kwargs)
    return factory

@pytest.fixture(scope='session')
def cart_line_item_factory():
    """Returns a factory to make cart line items."""
    return model_factory(CartLineItem)

@pytest.fixture(scope='session')
def seller_factory():
    """Returns a factory to make seller instances."""
    return model_factory(Seller)

def model_factory(model):
    """Returns a factory to make or prepare model instances."""
    def factory(*args, _save=True, **kwargs):
        if '_fill_optional' not in kwargs:
            kwargs['_fill_optional'] = True
        if _save:
            return baker.make(model, *args, **kwargs)
        else:
            return baker.prepare(model, *args, **kwargs)
    return factory
