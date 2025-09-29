from django.contrib.auth import get_user_model

from rest_framework import mixins
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import GenericViewSet

from .permissions import AccountPermission
from .serializers import UserSerializer


class AccountViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     GenericViewSet):
    """View set to create (register), retrieve and update accounts."""

    http_method_names = ['get', 'post', 'patch']

    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()
    permission_classes = (AccountPermission | IsAdminUser,)
