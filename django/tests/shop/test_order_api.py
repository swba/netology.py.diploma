import random
from collections import defaultdict

# noinspection PyPackageRequirements
import pytest

from apps.shop.models import Product, Order, CartLineItem
from apps.shop.serializers import (
    SellerSerializer,
    ShippingAddressSerializer,
    LineItemSerializer,
    OrderSerializer, ProductSerializer
)
from tests.utils import get_order_url, assert_response

@pytest.mark.django_db
def test_order_create__anonymous(api_client):
    """Test creating an order (anonymous user)."""
    response = api_client.post(get_order_url(), {})
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_order_create__no_shipping_address(api_client_auth):
    """Test creating an order (no shipping address provided)."""
    response = api_client_auth.post(get_order_url(), {})
    assert_response(response, 400, {
        'shipping_address_id': ["This field is required."],
    })

@pytest.mark.django_db
def test_order_create__wrong_shipping_address(api_client_auth,
        shipping_address_factory):
    """Test creating an order (shipping address belongs to someone else)."""
    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory()
    response = api_client_auth.post(get_order_url(), {
        'shipping_address_id': sa.id,
    })
    assert_response(response, 400, {
        'shipping_address_id': ["The shipping address either does not exist or belongs to another user."]
    })

@pytest.mark.django_db
def test_order_create__empty_cart(api_client_auth, shipping_address_factory):
    """Test creating an order (empty cart)."""
    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory(user=api_client_auth._user)
    response = api_client_auth.post(get_order_url(), {
        'shipping_address_id': sa.id,
    })
    assert_response(response, 400, {
        'detail': "The cart is empty.",
    })

@pytest.mark.django_db
def test_order_create__too_many(api_client_auth, product_factory,
        cart_line_item_factory, shipping_address_factory):
    """Test creating an order (product quantity is too large)."""
    product = product_factory()
    # noinspection PyUnresolvedReferences
    cart_line_item_factory(
        user=api_client_auth._user,
        product=product,
        quantity=product.quantity
    )

    product.quantity -= 1
    product.save()

    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory(user=api_client_auth._user)
    response = api_client_auth.post(get_order_url(), {
        'shipping_address_id': sa.id,
    })
    assert_response(response, 400, {
        'detail': "Quantity exceeds the stock.",
        'products': ProductSerializer([product], many=True).data,
    })

@pytest.mark.django_db
def test_order_create__seller_inactive(api_client_auth, seller_factory,
        product_factory, cart_line_item_factory, shipping_address_factory):
    """Test creating an order (product seller is not active)."""
    seller = seller_factory()
    product = product_factory(seller=seller)
    # noinspection PyUnresolvedReferences
    cart_line_item_factory(
        user=api_client_auth._user,
        product=product,
        quantity=product.quantity
    )

    seller.is_active = False
    seller.save()

    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory(user=api_client_auth._user)
    response = api_client_auth.post(get_order_url(), {
        'shipping_address_id': sa.id,
    })
    assert_response(response, 400, {
        'detail': "Seller is not active.",
        'products': ProductSerializer([product], many=True).data,
    })

@pytest.mark.django_db
def test_order_create(api_client_auth, user_factory, catalog_factory,
        shipping_address_factory, cart_line_item_factory, settings, mailoutbox):
    """Test creating an order."""
    settings.EMAIL_ASYNC = False # Do not use Celery for testing.

    catalog_factory()
    products = Product.objects.all()[:8]

    # Prepare several carts.
    # noinspection PyUnresolvedReferences
    cur_user = api_client_auth._user
    users = [cur_user, user_factory()]
    carts = defaultdict(list)
    for i, user in enumerate(users):
        for k in range(4):
            carts[i].append(cart_line_item_factory(
                user=user,
                product=products[i * 2 + k],
                quantity=random.randint(1, 10),
            ))

    # Order cart items for the current user.
    sa = shipping_address_factory(user=users[0])
    response = api_client_auth.post(get_order_url(), {
        'shipping_address_id': sa.id,
    })

    # Check email sent to the user.
    assert len(mailoutbox) > 0
    assert mailoutbox[0].subject == "The products have been ordered"
    print(mailoutbox[0].body)

    # Check that the cart was converted into a correct list of orders.
    expected = {}
    for line_item in carts[0]:
        seller = line_item.product.seller
        if seller.pk not in expected:
            expected[seller.pk] = {
                'id': len(expected) + 1,
                'seller': SellerSerializer(instance=seller).data,
                'shipping_address': ShippingAddressSerializer(instance=sa).data,
                'status': Order.Status.PENDING.value,
                'line_items': [],
            }
        expected[seller.pk]['line_items'].append(
            LineItemSerializer(instance=line_item).data
        )
    assert_response(response, 201, list(expected.values()))

    # Check that the cart is now empty.
    assert CartLineItem.objects.filter(user=cur_user).count() == 0

@pytest.mark.django_db
def test_order_list__anonymous(api_client):
    """Test listing orders (anonymous user)."""
    response = api_client.get(get_order_url())
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_order_list__user(api_client_auth, user_factory, order_factory,
        shipping_address_factory):
    """Test listing orders (as a regular user)."""
    orders = []
    # noinspection PyUnresolvedReferences
    for user in [api_client_auth._user, user_factory(), user_factory()]:
        sa = shipping_address_factory(user=user)
        for i in range(3):
            order = order_factory(shipping_address=sa)
            # noinspection PyUnresolvedReferences
            if user == api_client_auth._user:
                orders.append(order)
    expected = [OrderSerializer(instance=order).data for order in orders]
    response = api_client_auth.get(get_order_url())
    assert_response(response, 200, expected[::-1])

@pytest.mark.django_db
def test_order_list__seller(api_client_auth, user_factory, order_factory,
        seller_factory):
    """Test listing orders (as a seller)."""
    orders = []
    # noinspection PyUnresolvedReferences
    for user in [api_client_auth._user, user_factory(), user_factory()]:
        seller = seller_factory(user=user)
        for i in range(3):
            order = order_factory(seller=seller)
            # noinspection PyUnresolvedReferences
            if user == api_client_auth._user:
                orders.append(order)
    expected = [OrderSerializer(instance=order).data for order in orders]
    response = api_client_auth.get(get_order_url() + '?as_seller=true')
    assert_response(response, 200, expected[::-1])

@pytest.mark.django_db
def test_order_get__anonymous(api_client, order_factory):
    """Test retrieving order (anonymous user)."""
    order = order_factory()
    response = api_client.get(get_order_url(order.pk))
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_order_get__another_user(api_client_auth, order_factory,
        shipping_address_factory, user_factory):
    """Test retrieving order (as another user)."""
    sa = shipping_address_factory(user=user_factory())
    order = order_factory(shipping_address=sa)
    response = api_client_auth.get(get_order_url(order.pk))
    assert_response(response, 404, {
        'detail': "No Order matches the given query."
    })

@pytest.mark.django_db
def test_order_get__user(api_client_auth, order_factory,
        shipping_address_factory):
    """Test retrieving order (as a regular user)."""
    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory(user=api_client_auth._user)
    order = order_factory(shipping_address=sa)
    response = api_client_auth.get(get_order_url(order.pk))
    assert_response(response, 200, OrderSerializer(instance=order).data)

@pytest.mark.django_db
def test_order_get__seller(api_client_auth, order_factory, seller_factory):
    """Test retrieving order (as a seller)."""
    # noinspection PyUnresolvedReferences
    seller = seller_factory(user=api_client_auth._user)
    order = order_factory(seller=seller)
    response = api_client_auth.get(get_order_url(order.pk))
    assert_response(response, 200, OrderSerializer(instance=order).data)

@pytest.mark.django_db
def test_order_edit__anonymous(api_client, order_factory):
    """Test patching order (anonymous user)."""
    order = order_factory()
    response = api_client.patch(get_order_url(order.pk), {
        'status': Order.Status.CONFIRMED.value
    })
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_order_edit__another_user(api_client_auth, order_factory,
        shipping_address_factory, user_factory):
    """Test editing order (as another user)."""
    sa = shipping_address_factory(user=user_factory())
    order = order_factory(shipping_address=sa)
    response = api_client_auth.patch(get_order_url(order.pk), {
        'status': Order.Status.CONFIRMED.value
    })
    assert_response(response, 404, {
        'detail': "No Order matches the given query."
    })

@pytest.mark.django_db
def test_order_edit__user(api_client_auth, order_factory,
        shipping_address_factory):
    """Test editing order (as a regular user)."""
    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory(user=api_client_auth._user)
    order = order_factory(shipping_address=sa)
    response = api_client_auth.patch(get_order_url(order.pk), {
        'status': Order.Status.CONFIRMED.value
    })
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action."
    })

@pytest.mark.django_db
def test_order_edit__wrong_status(api_client_auth, order_factory, seller_factory):
    """Test editing order (setting incorrect status)."""
    # noinspection PyUnresolvedReferences
    seller = seller_factory(user=api_client_auth._user)
    order: Order = order_factory(seller=seller)

    statuses = {
        Order.Status.PENDING: Order.Status.COMPLETED,
        Order.Status.CONFIRMED: Order.Status.COMPLETED,
        Order.Status.SHIPPING: Order.Status.PENDING,
        Order.Status.COMPLETED: Order.Status.PENDING,
        Order.Status.CANCELED: Order.Status.PENDING,
    }

    for cur_status, new_status in statuses.items():
        order.status = cur_status
        order.save()

        response = api_client_auth.patch(get_order_url(order.pk), {
            'status': new_status.value,
        })
        assert_response(response, 400, {
            'status': [f"Allowed statuses: {', '.join(Order.status_workflow[cur_status])}"]
        })

@pytest.mark.django_db
def test_order_edit(api_client_auth, order_factory, seller_factory):
    """Test editing order."""
    # noinspection PyUnresolvedReferences
    seller = seller_factory(user=api_client_auth._user)
    order: Order = order_factory(seller=seller)

    statuses = {
        Order.Status.PENDING: Order.Status.CONFIRMED,
        Order.Status.CONFIRMED: Order.Status.SHIPPING,
        Order.Status.SHIPPING: Order.Status.COMPLETED,
    }

    for cur_status, new_status in statuses.items():
        order.status = cur_status
        order.save()

        response = api_client_auth.patch(get_order_url(order.pk), {
            'status': new_status.value,
        })
        assert_response(response, 200, OrderSerializer(instance=order).data | {
            'status': new_status.value,
        })
