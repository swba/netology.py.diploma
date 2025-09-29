from django_filters import rest_framework as filters

from .models import Product


class ProductFilter(filters.FilterSet):
    """Filters for products."""

    title = filters.CharFilter(
        field_name='title',
        lookup_expr='icontains')
    price = filters.RangeFilter(
        field_name='list_price')

    class Meta:
        model = Product
        fields = ['category', 'seller']
