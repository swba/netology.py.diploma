from rest_framework import permissions

from .models import User


class AccountPermission(permissions.DjangoModelPermissions):
    """Provides permission for accounts.

    The following rules are applied:
    - Respect model-level permissions first (inherited from
      DjangoModelPermissions).
    - Anonymous users can post (register).
    - Authenticated users can get and update their accounts.
    """

    def has_permission(self, request, view):
        perm = super().has_permission(request, view)
        if not perm and request.method == 'POST':
            perm = not request.user or not request.user.is_authenticated
        return perm

    def has_object_permission(self, request, view, obj: User):
        perm = super().has_permission(request, view)
        if not perm and request.method in ('PUT', 'PATCH', 'GET'):
            perm = request.user and request.user.pk == obj.pk
        return perm
