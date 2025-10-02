from rest_framework import serializers

from .models import (
    Category,
    Seller,
    Product,
    CartLineItem,
    ShippingAddress,
    Order
)


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


class LineItemProductSerializer(serializers.ModelSerializer):
    """Product serializer for line items."""

    class Meta:
        model = Product
        fields = ('id', 'title', 'slug', 'list_price')
        read_only_fields = ('id', 'title', 'list_price')


class LineItemSerializer(serializers.ModelSerializer):
    """General serializer for order and cart line items."""

    product = LineItemProductSerializer(read_only=True)

    class Meta:
        model = CartLineItem
        fields = ('id', 'product', 'quantity')
        read_only_fields = ('id',)


class CartLineItemCreateSerializer(LineItemSerializer):
    """Cart item serializer for create action."""

    product_id = serializers.IntegerField(min_value=1, write_only=True)

    class Meta(LineItemSerializer.Meta):
        fields = ('id', 'product_id', 'product', 'quantity')


class ShippingAddressSerializer(serializers.ModelSerializer):
    """Shipping address serializer."""

    class Meta:
        model = ShippingAddress
        fields = ('id', 'full_name', 'phone_number', 'street_address',
                  'locality', 'administrative_area', 'postal_code', 'country')
        read_only_fields = ('id',)


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for order create endpoint."""

    shipping_address_id = serializers.IntegerField(min_value=1, write_only=True)


class OrderSerializer(serializers.ModelSerializer):
    """Order serializer."""

    seller = SellerSerializer(read_only=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    line_items = LineItemSerializer(read_only=True, many=True)

    class Meta:
        model = Order
        fields = ('id', 'seller', 'shipping_address', 'status', 'line_items')
        read_only_fields = ('id',)

    def validate_status(self, value):
        """Validates order status."""
        if self.instance:
            allowed_statuses = Order.status_workflow[self.instance.status]
            if value not in allowed_statuses:
                raise serializers.ValidationError(
                    f"Allowed statuses: {', '.join(allowed_statuses)}"
                )
        return value
