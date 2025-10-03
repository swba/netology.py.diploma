from rest_framework.permissions import (
    IsAuthenticated,
    SAFE_METHODS,
    DjangoModelPermissionsOrAnonReadOnly
)

from .models import ShippingAddress, Order, Seller


class SellerPermission(DjangoModelPermissionsOrAnonReadOnly):
    """Provides permission for Seller model.

    Users must have Django's "Can add Seller Profile", "Can change
    Seller Profile" and "Can delete Seller Profile" permissions. This
    permission class ensures that users can only edit and delete their
    own seller profiles.
    """

    def has_object_permission(self, request, view, obj: Seller):
        if request.method not in SAFE_METHODS:
            return request.user and request.user.pk == obj.user.pk
        return super().has_object_permission(request, view, obj)


class ShippingAddressPermission(IsAuthenticated):
    """Provides permission for shipping addresses.

    Authenticated users can see and edit their own shipping addresses.
    Shipping addresses cannot be updated or deleted, if there are
    related orders.
    """

    def has_object_permission(self, request, view, obj: ShippingAddress):
        if request.user and request.user.pk == obj.user.pk:
            if request.method in ('PUT', 'PATCH', 'DELETE'):
                return not Order.objects.filter(shipping_address=obj.pk).exists()
            return True
        return False


class OrderPermission(IsAuthenticated):
    """Provides permission for orders.

    Authenticated users can view orders that they created.
    Sellers can view and update orders that are assigned to them.
    """

    def has_object_permission(self, request, view, obj: Order):
        return (request.user and
                ((request.user.pk == obj.shipping_address.user.pk and
                  request.method in SAFE_METHODS) or
                 request.user.pk == obj.seller.user.pk))
