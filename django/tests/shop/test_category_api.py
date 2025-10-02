# noinspection PyPackageRequirements
import pytest

from apps.shop.models import Category
from tests.utils import assert_response, get_category_url


def serialize_category(category: Category) -> dict:
    """Serializes a category.

    We serialize data manually and do not use a normal serializer here
    to be 100% sure we get proper results.
    """
    return {
        'id': category.pk,
        'slug': category.slug,
        'title': category.title,
    }

@pytest.mark.django_db
def test_category_list(api_client, category_factory):
    """Test listing categories."""
    categories = category_factory(_quantity=5)
    url = get_category_url()

    expected = [serialize_category(category) for category in categories]
    expected.sort(key=lambda item: item['title'])

    response = api_client.get(url)
    assert_response(response, 200, expected)

@pytest.mark.django_db
def test_category_get__not_exists(api_client):
    """Test retrieving category (not existing)."""
    url = get_category_url(1)

    response = api_client.get(url)
    assert_response(response, 404, {
        'detail': "No Category matches the given query."
    })

@pytest.mark.django_db
def test_category_get(api_client, category_factory):
    """Test retrieving category."""
    category = category_factory()
    url = get_category_url(category.pk)

    response = api_client.get(url)
    assert_response(response, 200, serialize_category(category))
