# noinspection PyPackageRequirements
import pytest

from tests.utils import get_shipping_address_url, assert_response

@pytest.mark.django_db
def test_shipping_address_add__anonymous(api_client):
    """Test adding a shipping address (anonymous user)."""
    response = api_client.post(get_shipping_address_url(), {})
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_shipping_address_add__no_data(api_client_auth):
    """Test adding a shipping address (no data)."""
    response = api_client_auth.post(get_shipping_address_url(), {})
    assert_response(response, 400, {
        'full_name': ["This field is required."],
        'street_address': ["This field is required."],
        'locality': ["This field is required."],
        'postal_code': ["This field is required."],
        'country': ["This field is required."]
    })

@pytest.mark.django_db
def test_shipping_address_add__partial_data(api_client_auth):
    """Test adding a shipping address (some data is missing)."""
    response = api_client_auth.post(get_shipping_address_url(), {
        'full_name': "Michael Jordan",
        'locality': "Chicago",
        'country': "United States",
    })
    assert_response(response, 400, {
        'street_address': ["This field is required."],
        'postal_code': ["This field is required."],
    })

@pytest.mark.django_db
def test_shipping_address_add__wrong_phone(api_client_auth, shipping_address_factory):
    """Test adding a shipping address (incorrect phone number format)."""
    sa = shipping_address_factory(_save=False)
    data = {
        'full_name': sa.full_name,
        'phone_number': '223322223322',
        'street_address': sa.street_address,
        'locality': sa.locality,
        'administrative_area': sa.administrative_area,
        'postal_code': sa.postal_code,
        'country': sa.country,
    }
    response = api_client_auth.post(get_shipping_address_url(), data)
    assert_response(response, 400, {
        'phone_number': ["Enter a valid value."],
    })

@pytest.mark.django_db
def test_shipping_address_add(api_client_auth, shipping_address_factory):
    """Test adding a shipping address."""
    sa = shipping_address_factory(_save=False)
    data = {
        'full_name': sa.full_name,
        'phone_number': sa.phone_number,
        'street_address': sa.street_address,
        'locality': sa.locality,
        'administrative_area': sa.administrative_area,
        'postal_code': sa.postal_code,
        'country': sa.country,
    }
    response = api_client_auth.post(get_shipping_address_url(), data)
    assert_response(response, 201, data | {
        'id': 1,
    })

@pytest.mark.django_db
def test_shipping_address_get__anonymous(api_client, shipping_address_factory):
    """Test getting a shipping address (anonymous request)."""
    sa = shipping_address_factory()
    response = api_client.get(get_shipping_address_url(sa.pk))
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_shipping_address_get__another_user(api_client_auth, shipping_address_factory):
    """Test getting a shipping address (under another account)."""
    sa = shipping_address_factory() # Created for a new random user.
    response = api_client_auth.get(get_shipping_address_url(sa.pk))
    assert_response(response, 404, {
        'detail': "No ShippingAddress matches the given query."
    })

@pytest.mark.django_db
def test_shipping_address_get(api_client_auth, shipping_address_factory):
    """Test getting a shipping address."""
    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory(user=api_client_auth._user)
    response = api_client_auth.get(get_shipping_address_url(sa.pk))
    assert_response(response, 200, {
        'id': sa.pk,
        'full_name': sa.full_name,
        'phone_number': sa.phone_number,
        'street_address': sa.street_address,
        'locality': sa.locality,
        'administrative_area': sa.administrative_area,
        'postal_code': sa.postal_code,
        'country': sa.country,
    })

@pytest.mark.django_db
def test_shipping_address_patch__anonymous(api_client, shipping_address_factory):
    """Test patching a shipping address (anonymous request)."""
    sa = shipping_address_factory()
    response = api_client.patch(get_shipping_address_url(sa.pk), {})
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_shipping_address_patch__another_user(api_client_auth, shipping_address_factory):
    """Test patching a shipping address (under another account)."""
    sa = shipping_address_factory() # Created for a new random user.
    response = api_client_auth.patch(get_shipping_address_url(sa.pk), {})
    assert_response(response, 404, {
        'detail': "No ShippingAddress matches the given query."
    })

@pytest.mark.django_db
def test_shipping_address_patch__order_exists(api_client_auth, shipping_address_factory, order_factory):
    """Test patching a shipping address (with existing order)."""
    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory(user=api_client_auth._user)
    order_factory(shipping_address=sa)
    response = api_client_auth.patch(get_shipping_address_url(sa.pk), {})
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action."
    })

@pytest.mark.django_db
def test_shipping_address_patch(api_client_auth, shipping_address_factory):
    """Test patching a shipping address."""
    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory(user=api_client_auth._user)
    response = api_client_auth.patch(get_shipping_address_url(sa.pk), {
        'full_name': "Lemmy",
        'country': "Great Britain",
    })
    assert_response(response, 200, {
        'id': sa.pk,
        'full_name': "Lemmy",
        'phone_number': sa.phone_number,
        'street_address': sa.street_address,
        'locality': sa.locality,
        'administrative_area': sa.administrative_area,
        'postal_code': sa.postal_code,
        'country': "Great Britain",
    })

@pytest.mark.django_db
def test_shipping_address_delete__anonymous(api_client, shipping_address_factory):
    """Test deleting a shipping address (anonymous request)."""
    sa = shipping_address_factory()
    response = api_client.delete(get_shipping_address_url(sa.pk))
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_shipping_address_delete__another_user(api_client_auth, shipping_address_factory):
    """Test deleting a shipping address (under another account)."""
    sa = shipping_address_factory() # Created for a new random user.
    response = api_client_auth.delete(get_shipping_address_url(sa.pk))
    assert_response(response, 404, {
        'detail': "No ShippingAddress matches the given query."
    })

@pytest.mark.django_db
def test_shipping_address_delete__order_exists(api_client_auth, shipping_address_factory, order_factory):
    """Test deleting a shipping address (with existing order)."""
    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory(user=api_client_auth._user)
    order_factory(shipping_address=sa)
    response = api_client_auth.delete(get_shipping_address_url(sa.pk))
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action."
    })

@pytest.mark.django_db
def test_shipping_address_delete(api_client_auth, shipping_address_factory):
    """Test deleting a shipping address."""
    # noinspection PyUnresolvedReferences
    sa = shipping_address_factory(user=api_client_auth._user)
    # The shipping address is here.
    response = api_client_auth.get(get_shipping_address_url(sa.pk))
    assert response.status_code == 200
    # Delete it.
    response = api_client_auth.delete(get_shipping_address_url(sa.pk))
    assert response.status_code == 204
    # The shipping address is gone.
    response = api_client_auth.get(get_shipping_address_url(sa.pk))
    assert_response(response, 404, {
        'detail': "No ShippingAddress matches the given query."
    })

@pytest.mark.django_db
def test_shipping_address_list(api_client_auth, user_factory, shipping_address_factory):
    """Test getting a list of shipping addresses."""
    expected = []

    # Create several shipping addresses for several users.
    # noinspection PyUnresolvedReferences
    users = [api_client_auth._user, user_factory(), user_factory()]
    for i in range(9):
        sa = shipping_address_factory(user=users[i % 3])
        if i % 3 == 0:
            expected.append({
                'id': sa.pk,
                'full_name': sa.full_name,
                'phone_number': sa.phone_number,
                'street_address': sa.street_address,
                'locality': sa.locality,
                'administrative_area': sa.administrative_area,
                'postal_code': sa.postal_code,
                'country': sa.country,
            })

    response = api_client_auth.get(get_shipping_address_url())
    assert_response(response, 200, expected[::-1])
