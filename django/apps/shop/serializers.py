from rest_framework import serializers

from .models import Category, Seller, Product


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer."""

    class Meta:
        model = Category
        fields = ('id', 'title', 'slug')
        read_only_fields = ('id', 'slug')


class SellerSerializer(serializers.ModelSerializer):
    """Seller serializer."""

    class Meta:
        model = Seller
        fields = ('id', 'title', 'website_url', 'business_info', 'is_active')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    """Product serializer."""

    category = CategorySerializer(read_only=True)
    seller = SellerSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'title', 'slug', 'category', 'seller', 'model',
                  'quantity', 'list_price')
        read_only_fields = ('id', 'slug')
