from django.db import IntegrityError
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .filters import ProductFilter
from .models import Product, CartLineItem
from .serializers import (
    ProductSerializer,
    CartLineItemSerializer,
    CartLineItemCreateSerializer
)


class ProductViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     GenericViewSet):
    """View set to retrieve products."""

    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    filterset_class = ProductFilter
    pagination_class = PageNumberPagination


@extend_schema_view(
    list=extend_schema(description="Get the full cart."),
    create=extend_schema(
        description="Adds a new line item to the cart. Returns the full cart.",
        responses={
            status.HTTP_201_CREATED: CartLineItemSerializer(many=True),
        }
    ),
    partial_update=extend_schema(
        description="Updates a cart line item's quantity. Returns the full cart.",
        responses={
            status.HTTP_200_OK: CartLineItemSerializer(many=True),
        }
    ),
    destroy=extend_schema(
        description="Deletes a cart line item. Returns the full cart.",
        responses={
            status.HTTP_200_OK: CartLineItemSerializer(many=True),
        }
    ),
    clear=extend_schema(
        operation_id='cart_clear',
        description="Clears the cart.",
        responses={
            status.HTTP_200_OK: CartLineItemSerializer(many=True),
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

    serializer_class = CartLineItemSerializer
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
