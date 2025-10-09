import json
from contextlib import contextmanager
from typing import Literal

# noinspection PyPackageRequirements
import pytest
import yaml
from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.base.utils import slugify
from apps.shop.models import Product, Category
from tests.utils import get_import_url, assert_response


PRODUCTS_FILENAME = 'products'


def grant_permission(user: User, permission: Literal['add', 'change', 'delete']):
    """Grants given seller permission to the user."""
    p = Permission.objects.get(codename=f'{permission}_seller')
    user.user_permissions.add(p)

def get_file_path(filename: str) -> str:
    """Returns path to a file with test data."""
    return settings.BASE_DIR / 'tests' / 'shop' / 'data' / 'products' / filename

def parse_file(filename: str) -> dict|None:
    """Parses file with text data."""
    with open(get_file_path(filename), encoding='utf-8') as file:
        ext = filename.split('.')[-1]
        if ext == 'json':
            return json.load(file)
        elif ext == 'yaml':
            return yaml.full_load(file)
        else:
            return None

@contextmanager
def uploaded_file(filename: str):
    """Context manager that creates an uploaded file with test data."""
    with open(get_file_path(filename), 'rb') as f:
        yield SimpleUploadedFile(f.name, f.read(), content_type='text/plain')


@pytest.mark.django_db
def test_upload__anonymous(api_client: APIClient):
    """Test uploading seller products (anonymous user)."""
    response = api_client.post(get_import_url(), {})
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_upload__not_owner(api_client_auth: APIClient, seller_factory,
        user_factory):
    """Test uploading seller products (seller belongs to another user)."""
    seller = seller_factory(user=user_factory())
    response = api_client_auth.post(get_import_url(), {
        'seller': seller.pk,
        'url': 'https://fake.site/data.json',
        'format': 'json',
    })
    assert_response(response, 400, {
        'seller': [f'Invalid pk "{seller.pk}" - object does not exist.']
    })

@pytest.mark.django_db
def test_upload__no_url_file(api_client_auth: APIClient, seller_factory,
        user_factory):
    """Test uploading seller products (no URL of file provided)."""
    # noinspection PyUnresolvedReferences
    seller = seller_factory(user=api_client_auth._user)

    response = api_client_auth.post(get_import_url(), {
        'seller': seller.pk,
        'format': 'json',
    })
    assert_response(response, 400, {
        'non_field_errors': ["URL or file is required."]
    })

@pytest.mark.django_db
def test_upload__no_format(api_client_auth: APIClient, seller_factory,
        user_factory):
    """Test uploading seller products (missing format field)."""
    # noinspection PyUnresolvedReferences
    seller = seller_factory(user=api_client_auth._user)

    response = api_client_auth.post(get_import_url(), {
        'seller': seller.pk,
        'url': 'https://fake.site/data.json',
    })
    assert_response(response, 400, {
        'format': ["This field is required."]
    })

@pytest.mark.django_db
def test_upload__wrong_format(api_client_auth: APIClient, seller_factory,
        user_factory):
    """Test uploading seller products (incorrect format)."""
    # noinspection PyUnresolvedReferences
    seller = seller_factory(user=api_client_auth._user)

    response = api_client_auth.post(get_import_url(), {
        'seller': seller.pk,
        'url': 'https://fake.site/data.json',
        'format': 'pdf',
    })
    assert_response(response, 400, {
        'format': ["Only `yaml` or `json` format is supported."]
    })

@pytest.mark.django_db
def test_upload__no_categories(api_client_auth: APIClient, seller_factory):
    """Test uploading seller products (no categories)."""
    # noinspection PyUnresolvedReferences
    seller = seller_factory(user=api_client_auth._user)

    for ext in ('yaml', 'json'):
        expected = []
        for row in parse_file(f'{PRODUCTS_FILENAME}.{ext}'):
            if 'category_id' in row:
                category_id = row['category_id']
                expected.append({
                    'category_id': [f'Invalid pk "{category_id}" - object does not exist.']
                })
            elif 'category_slug' in row:
                category_slug = row['category_slug']
                expected.append({
                    'category_slug': [f"Object with slug={category_slug} does not exist."]
                })
            else:
                category_slug = slugify(row['category_title'])
                expected.append({
                    'category_title': [f"Object with slug={category_slug} does not exist."]
                })

        with uploaded_file(f'{PRODUCTS_FILENAME}.{ext}') as file:
            response = api_client_auth.post(get_import_url(), {
                'seller': seller.pk,
                'format': ext,
                'file': file,
            })
            assert_response(response, 400, expected)

@pytest.mark.django_db
def test_upload__invalid_data(api_client_auth: APIClient, category_factory,
        seller_factory):
    """Test uploading seller products (invalid data)."""
    category_factory(),
    # noinspection PyUnresolvedReferences
    seller = seller_factory(user=api_client_auth._user)

    for ext in ('yaml', 'json'):
        with uploaded_file(f'{PRODUCTS_FILENAME}__invalid.{ext}') as file:
            response = api_client_auth.post(get_import_url(), {
                'seller': seller.pk,
                'format': ext,
                'file': file,
            })
            assert_response(response, 400, [
                {'non_field_errors': [
                    "One of `category_id`, `category_slug` or `category_title` "
                    "field must be provided."
                ]},
                {'non_field_errors': [
                    "Either `id` or `external_id` field must be provided."
                ]}
            ])

@pytest.mark.django_db
def test_upload__success(api_client_auth, category_factory, seller_factory,
        product_factory):
    """Test uploading seller products (success)."""
    # Create required categories.
    category_factory(title="Смартфоны"),
    category_factory(title="Телевизоры"),
    category_factory(title="Flash-накопители")

    # Create several products for another user and seller.
    seller = seller_factory()
    product_factory(seller=seller, _quantity=5)

    # Create a couple of sellers for the current user.
    # noinspection PyUnresolvedReferences
    seller_factory(user=api_client_auth._user)
    # noinspection PyUnresolvedReferences
    seller = seller_factory(user=api_client_auth._user)

    for ext in ('yaml', 'json'):
        with uploaded_file(f'{PRODUCTS_FILENAME}.{ext}') as file:
            response = api_client_auth.post(get_import_url(), {
                'seller': seller.pk,
                'format': ext,
                'file': file,
            })
            assert_response(response, 200, {'detail': "Import completed."})

        data = parse_file(f'{PRODUCTS_FILENAME}.{ext}')
        products = Product.objects.filter(seller=seller)

        # Check that all products were added.
        assert len(data) == products.count()

        # Check that all added products have required external IDs.
        external_ids = [item['external_id'] for item in data]
        assert len(data) == products.filter(external_id__in=external_ids).count()

        # Check that all added products have required titles.
        titles = [item['title'] for item in data]
        assert len(data) == products.filter(title__in=titles).count()

        # Check that all added products belong to proper categories.
        for item in data:
            if 'category_id' in item:
                category = Category.objects.get_or_none(pk=item['category_id'])
            elif 'category_slug' in item:
                category = Category.objects.get_or_none(slug=item['category_slug'])
            else:
                category = Category.objects.get_or_none(title=item['category_title'])
            kwargs = {'external_id': item['external_id'], 'category': category}
            assert products.filter(**kwargs).count() == 1

        # Check that all products have a proper set of parameters.
        for item in data:
            product = products.get(external_id=item['external_id'])
            parameters = {p.name: p.value for p in product.parameters.all()}
            # All parameters' values are string, so convert them.
            expected = {n: str(v) for n, v in item['parameters'].items()}
            assert expected == parameters
