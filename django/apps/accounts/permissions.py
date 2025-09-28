from rest_framework.permissions import IsAuthenticated

from .models import User


class AccountPermission(IsAuthenticated):
    """Provides permission for accounts.

    The following rules are applied:
    - Anonymous users can post (register).
    - Authenticated users can get and update their accounts.
    """

    def has_permission(self, request, view):
        perm = super().has_permission(request, view)
        return not perm if request.method == 'POST' else perm

    def has_object_permission(self, request, view, obj: User):
        if request.method in ('PUT', 'PATCH', 'GET'):
            return request.user and request.user.pk == obj.pk
        return False
