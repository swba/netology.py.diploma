# noinspection PyPackageRequirements
import pytest
from rest_framework.test import APIClient

from apps.shop.models import Product, Category, Seller
from tests.utils import get_product_url, get_random_substring, assert_response_count, get_random_price_range


@pytest.mark.django_db
def test_product_search__all(api_client: APIClient, catalog_factory):
    """Test product search (all records)."""
    catalog_factory()
    url = get_product_url()

    response = api_client.get(url)
    assert_response_count(
        response, 200,
        len(Product.objects.all().paginate().get_page(1))
    )

@pytest.mark.django_db
def test_product_search__title(api_client: APIClient, catalog_factory):
    """Test product search (by product title)."""
    catalog_factory()
    url = get_product_url()

    title = Product.objects.first().title
    for n in range(1, 6):
        query = get_random_substring(title, n)
        response = api_client.get(url, {'title': query})
        assert_response_count(
            response, 200,
            len(Product.objects.filter(title__icontains=query).paginate().get_page(1))
        )

@pytest.mark.django_db
def test_product_search__category(api_client: APIClient, catalog_factory):
    """Test product search (by category)."""
    catalog_factory()
    url = get_product_url()

    for category in Category.objects.all():
        response = api_client.get(url, {'category': category.pk})
        assert_response_count(
            response, 200,
            len(Product.objects.filter(category=category.pk).paginate().get_page(1))
        )

@pytest.mark.django_db
def test_product_search__seller(api_client: APIClient, catalog_factory):
    """Test product search (by seller)."""
    catalog_factory()
    url = get_product_url()

    for seller in Seller.objects.all():
        response = api_client.get(url, {'seller': seller.pk})
        assert_response_count(
            response, 200,
            len(Product.objects.filter(seller=seller.pk).paginate().get_page(1))
        )

@pytest.mark.django_db
def test_product_search__price(api_client: APIClient, catalog_factory):
    """Test product search (by price)."""
    catalog_factory()
    url = get_product_url()

    p1, p2 = get_random_price_range()

    # Check minimum price.
    response = api_client.get(url, {'price_min': p1})
    assert_response_count(
        response, 200,
        len(Product.objects.filter(list_price__gte=p1).paginate().get_page(1))
    )

    # Check maximum price.
    response = api_client.get(url, {'price_max': p2})
    assert_response_count(
        response, 200,
        len(Product.objects.filter(list_price__lte=p2).paginate().get_page(1))
    )

    # Check price range.
    response = api_client.get(url, {'price_min': p1, 'price_max': p2})
    assert_response_count(
        response, 200,
        len(Product.objects.filter(
            list_price__gte=p1,
            list_price__lte=p2
        ).paginate().get_page(1))
    )

@pytest.mark.django_db
def test_product_search__complex(api_client: APIClient, catalog_factory):
    """Test product search (complex search)."""
    catalog_factory()
    url = get_product_url()

    for category in Category.objects.all():
        for seller in Seller.objects.all():
            p1, p2 = get_random_price_range()
            response = api_client.get(url, {
                'category': category.pk,
                'seller': seller.pk,
                'price_min': p1,
                'price_max': p2
            })
            assert_response_count(
                response, 200,
                len(Product.objects.filter(
                    category=category.pk,
                    seller=seller.pk,
                    list_price__gte=p1,
                    list_price__lte=p2
                ).paginate().get_page(1))
            )
