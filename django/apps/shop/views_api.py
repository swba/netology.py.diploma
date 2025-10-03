from django.db import IntegrityError
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .filters import ProductFilter
from .models import Product, CartLineItem, ShippingAddress, Order, Category
from .permissions import ShippingAddressPermission, OrderPermission
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    LineItemSerializer,
    CartLineItemCreateSerializer,
    ShippingAddressSerializer,
    OrderSerializer,
    OrderCreateSerializer,
)


@extend_schema_view(
    list=extend_schema(description="List all catalog categories."),
    retrieve=extend_schema(description="Get category details."),
)
class CategoryViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      GenericViewSet):
    """View set to list and retrieve categories."""

    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class ProductViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     GenericViewSet):
    """View set to retrieve products."""

    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    filterset_class = ProductFilter
    pagination_class = PageNumberPagination


@extend_schema_view(
    list=extend_schema(description="Get the current user's cart."),
    create=extend_schema(
        description="Add a new line item to the current user's cart.",
        responses={
            status.HTTP_201_CREATED: LineItemSerializer(many=True),
        }
    ),
    partial_update=extend_schema(
        description="Update a cart line item's quantity.",
        responses={
            status.HTTP_200_OK: LineItemSerializer(many=True),
        }
    ),
    destroy=extend_schema(
        description="Delete a cart line item.",
        responses={
            status.HTTP_200_OK: LineItemSerializer(many=True),
        }
    ),
    clear=extend_schema(
        operation_id='cart_clear',
        description="Clears the current user's cart.",
        responses={
            status.HTTP_200_OK: LineItemSerializer(many=True),
        }
    )
)
class CartLineItemViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin,
                          GenericViewSet):
    """View set to create, list, update and delete cart line items.
    """
    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = LineItemSerializer
    queryset = CartLineItem.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'create':
            return CartLineItemCreateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        # Always work with the current user's cart.
        return super().get_queryset().filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {'detail': "Product is already in the cart."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Return the full cart after adding a line item.
        return self.get_cart(status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        # Always add items to the current user's cart.
        serializer.save(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        # Return the full cart after updating a line item.
        return self.get_cart()

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        # Return the full cart after deleting a line item.
        return self.get_cart()

    # noinspection PyUnusedLocal
    @action(detail=False, methods=['delete'], url_path='all')
    def clear(self, request):
        """Clears the current user's cart."""
        self.get_queryset().delete()
        return self.get_cart()

    def get_cart(self, status_code: int = status.HTTP_200_OK):
        """Returns all the current user's cart line items."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status_code)


@extend_schema_view(
    list=extend_schema(description="Get a list of shipping addresses."),
    retrieve=extend_schema(description="Get shipping addresses details."),
    create=extend_schema(description="Add a new shipping address."),
    partial_update=extend_schema(description="Update a shipping address."),
    destroy=extend_schema(description="Delete a shipping address.")
)
class ShippingAddressViewSet(ModelViewSet):
    """View set for shipping addresses.

    Shipping addresses cannot be updated or deleted, if there are
    related orders. To edit a shipping address, all related orders
    must be removed or unbound first.
    """

    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = ShippingAddressSerializer
    queryset = ShippingAddress.objects.all()
    permission_classes = (ShippingAddressPermission,)

    def get_queryset(self):
        # Always work with the current user.
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        # Always create shipping addresses for the current user.
        serializer.save(user=self.request.user)


@extend_schema_view(
    create=extend_schema(
        description="Create new orders from the cart contents.",
        request=OrderCreateSerializer,
        parameters=[
            OpenApiParameter(
                name='as_seller',
                description="Show orders assigned to the current user as a seller",
                required=False,
                type=OpenApiTypes.BOOL,
            ),
        ],
        responses=OrderSerializer(many=True),
    ),
    list=extend_schema(description="Get a list of orders."),
    retrieve=extend_schema(description="Get order details."),
    partial_update=extend_schema(description="Update order status."),
)
class OrderViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   GenericViewSet):
    """View set to get and edit orders."""

    http_method_names = ['post', 'get', 'patch']

    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    permission_classes = (OrderPermission,)

    def get_queryset(self):
        if self.action == 'list':
            # Sellers can view orders assigned to them.
            if self.request.query_params.get('as_seller'):
                return super().get_queryset().filter(
                    seller__user=self.request.user
                )
            # Regular user can view orders created by them.
            else:
                return super().get_queryset().filter(
                    shipping_address__user=self.request.user
                )
        else:
            return super().get_queryset().filter(
                Q(seller__user=self.request.user) |
                Q(shipping_address__user=self.request.user)
            )

    # noinspection PyMethodMayBeStatic
    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipping_address_id = serializer.validated_data['shipping_address_id']

        # Check if the shipping address belongs to the current user.
        shipping_address_is_valid = ShippingAddress.objects.filter(
            pk=shipping_address_id,
            user=self.request.user
        ).exists()
        if not shipping_address_is_valid:
            raise ValidationError({
                'shipping_address_id': ["The shipping address either does not exist or belongs to another user."]
            })

        # Check if the cart is not empty.
        if not CartLineItem.objects.filter(user=self.request.user).exists():
            return Response(
                {'detail': "The cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = (CartLineItem.objects.filter(user=self.request.user)
                .select_related('product'))

        # Check if product quantities are still valid.
        exceedances = []
        for cart_line_item in cart: # type: CartLineItem
            if cart_line_item.quantity > cart_line_item.product.quantity:
                exceedances.append(cart_line_item.product)
        if exceedances:
            return Response(
                {
                    'detail': "Quantity exceeds the stock.",
                    'products': ProductSerializer(exceedances, many=True).data,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Group all cart line items into orders by seller.
        orders = {}
        for cart_line_item in cart: # type: CartLineItem
            seller_id = cart_line_item.product.seller_id
            # Create a new order for the current seller, if needed.
            if seller_id not in orders:
                orders[seller_id] = Order.objects.create(
                    seller_id=seller_id,
                    shipping_address_id=shipping_address_id
                )
            # Copy line item from the cart to the order.
            orders[seller_id].line_items.create(
                product=cart_line_item.product,
                quantity=cart_line_item.quantity,
            )
        # Clear the cart.
        cart.delete()

        serializer = OrderSerializer(orders.values(), many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
