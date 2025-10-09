from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.base.utils import slugify

from .models import (
    Category,
    Seller,
    Product,
    CartLineItem,
    ShippingAddress,
    Order, ProductParameter
)


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer."""

    class Meta:
        model = Category
        fields = ('id', 'title', 'slug')
        read_only_fields = ('id', 'title', 'slug')


class SellerSerializer(serializers.ModelSerializer):
    """Seller serializer."""

    class Meta:
        model = Seller
        fields = ('id', 'title', 'website_url', 'business_info', 'is_active')
        read_only_fields = ('id',)


class ProductParameterSerializer(serializers.ModelSerializer):
    """Product parameter serializer."""

    class Meta:
        model = ProductParameter
        fields = ('id', 'name', 'value')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    """Product serializer."""

    category = CategorySerializer(
        read_only=True)
    seller = SellerSerializer(
        read_only=True)
    parameters = ProductParameterSerializer(
        many=True,
        read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'title', 'slug', 'category', 'seller', 'model',
                  'quantity', 'list_price', 'parameters')
        read_only_fields = ('id', 'slug')


class LineItemProductSerializer(serializers.ModelSerializer):
    """Product serializer for line items."""

    class Meta:
        model = Product
        fields = ('id', 'title', 'slug', 'list_price')
        read_only_fields = ('id', 'title', 'list_price')


class LineItemSerializer(serializers.ModelSerializer):
    """General serializer for order and cart line items."""

    product = LineItemProductSerializer(
        read_only=True)

    class Meta:
        model = CartLineItem
        fields = ('id', 'product', 'quantity', 'total')
        read_only_fields = ('id',)

    def validate(self, attrs):
        # Validate that the product's seller is still active.
        if self.instance:
            seller_is_active = Seller.objects.filter(
                is_active=True,
                products=self.instance.product
            ).exists()
            if not seller_is_active:
                raise serializers.ValidationError({
                    'product': "Seller is not active."
                })

        # Validate quantity (cannot be greater than product stock).
        if quantity := attrs.get('quantity'):
            product = None
            if self.instance:
                product = self.instance.product
            elif product_id := attrs.get('product_id'):
                product = Product.objects.get(id=product_id)
            if product:
                if quantity > product.quantity:
                    raise serializers.ValidationError({
                        'quantity': "Quantity exceeds the stock."
                    })

        return super().validate(attrs)


class CartLineItemCreateSerializer(LineItemSerializer):
    """Cart item serializer for create action."""

    product_id = serializers.IntegerField(min_value=1, write_only=True)

    class Meta(LineItemSerializer.Meta):
        fields = ('id', 'product_id', 'product', 'quantity')

    # noinspection PyMethodMayBeStatic
    def validate_product_id(self, value):
        """Checks that product exists and its seller is active."""
        # Check product.
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product does not exist.")
        # Check seller.
        seller_is_active = Seller.objects.filter(
            is_active=True,
            products__id=value
        ).exists()
        if not seller_is_active:
            raise serializers.ValidationError("Seller is not active.")
        return value


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

    seller = SellerSerializer(
        read_only=True)
    shipping_address = ShippingAddressSerializer(
        read_only=True)
    line_items = LineItemSerializer(
        read_only=True,
        many=True)

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


class UserFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """A PK-related field with queryset filtered by the current user."""

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return queryset.filter(user=request.user)
        return queryset.none()


class SellerFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """A PK-related field with queryset filtered by seller."""

    def get_queryset(self):
        queryset = super().get_queryset()
        if seller_id := self.context.get('seller_id', None):
            return queryset.filter(seller_id=seller_id)
        return queryset.none()


class SlugSourceRelatedField(serializers.SlugRelatedField):
    """A field that gets slugified to represent a slug relationship."""

    def to_internal_value(self, data):
        data = slugify(data)
        return super().to_internal_value(data)


class CatalogImportSerializer(serializers.Serializer):
    """Catalog import serializer."""

    seller = UserFilteredPrimaryKeyRelatedField(
        queryset=Seller.objects.all())
    url = serializers.URLField(
        required=False)
    file = serializers.FileField(
        required=False)
    format = serializers.CharField()

    # noinspection PyMethodMayBeStatic
    def validate_format(self, value):
        """Validates format value."""
        if value not in ('yaml', 'json'):
            raise serializers.ValidationError("Only `yaml` or `json` format is supported.")
        return value

    def validate(self, attrs):
        if 'url' not in attrs and 'file' not in attrs:
            raise serializers.ValidationError("URL or file is required.")
        return super().validate(attrs)


class ProductImportSerializer(serializers.ModelSerializer):
    """Product import serializer."""

    id = SellerFilteredPrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        required=False,
        help_text="Product ID.")
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        help_text="Category ID.")
    # Allows providing category slug instead of category ID.
    category_slug = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug',
        required=False,
        help_text=_("Category slug to be used instead of ID to look for "
                    "the category object."))
    # Allows providing category title instead of category ID.
    category_title = SlugSourceRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug',
        required=False,
        help_text=_("Category title to be used instead of ID or slug. Will be "
                    "slugified before looking for category. If not found, a "
                    "slug-related error is returned."))
    parameters = serializers.DictField(
        required=False,
        help_text=_("Dict of product parameters."))

    class Meta:
        model = Product
        fields = ('id', 'external_id', 'title', 'category_id', 'category_slug',
                  'category_title', 'model', 'quantity', 'price', 'list_price',
                  'parameters')

    def validate(self, attrs):
        # Check that we have some category data.
        if ('category_id' not in attrs and
                'category_slug' not in attrs and
                'category_title' not in attrs):
            raise serializers.ValidationError(
                "One of `category_id`, `category_slug` or `category_title` "
                "field must be provided."
            )
        # Check that there is either internal or external product ID.
        if 'id' not in attrs and 'external_id' not in attrs:
            raise serializers.ValidationError(
                "Either `id` or `external_id` field must be provided."
            )
        return super().validate(attrs)


class ProductCreateSerializer(serializers.ModelSerializer):
    """Product create serializer."""

    class Meta:
        model = Product
        fields = ('external_id', 'title', 'category', 'model', 'quantity',
                  'price', 'list_price', 'seller')
