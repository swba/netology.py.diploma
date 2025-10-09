from typing import Literal

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_view, extend_schema

from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.base.email import send_email, EmailParams

from .models import UserToken, User
from .permissions import AccountPermission
from .serializers import (
    UserSerializer,
    UserPasswordSerializer,
    AccountEmailVerifySerializer,
    AccountPasswordRestoreSerializer
)
from ..base.serializers import BaseResponseSerializer

# Types of actions that require a valid token for verification.
ProtectedActions = Literal['verify', 'restore']


@extend_schema_view(
    create=extend_schema(description="Register a new account."),
    retrieve=extend_schema(description="Retrieve account details."),
    patch=extend_schema(description="Update account details."),
    verify=extend_schema(
        request=AccountEmailVerifySerializer,
        responses={
            status.HTTP_200_OK: BaseResponseSerializer,
            status.HTTP_404_NOT_FOUND: BaseResponseSerializer,
        },
        description="If `token` value is not provided, a new verification "
                    "email is sent to the account's email address, otherwise "
                    "it's used to verify the address."
    ),
    restore=extend_schema(
        request=AccountPasswordRestoreSerializer,
        responses={
            status.HTTP_200_OK: BaseResponseSerializer,
            status.HTTP_404_NOT_FOUND: BaseResponseSerializer,
        },
        description="If `token` value is not provided, a new email with a "
                    "restoration token is sent to the account's email address, "
                    "otherwise it's used to reset the account's password."
    ),
)
class AccountViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     GenericViewSet):
    """View set to create (register), retrieve and update accounts."""

    http_method_names = ['get', 'post', 'patch']

    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()
    permission_classes = (AccountPermission | IsAdminUser,)

    def perform_create(self, serializer):
        # Require email confirmation if the user is registered via API.
        # We don't use signals for this, because users created via
        # admin UI most likely won't require email confirmation even if
        # created inactive.
        user = serializer.save(is_active=False, is_verified=False)
        self.send_token_email(user, 'verify')

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def verify(self, request, pk=None):
        """Endpoint to verify user's email address."""
        def verify_email(user) -> str:
            user.is_verified = True
            user.save()
            return "Email verified."
        return self.protected_action(request, pk, 'verify', verify_email)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def restore(self, request, pk=None):
        """Endpoint to restore user's password."""
        def reset_password(user) -> str:
            serializer = UserPasswordSerializer(
                data=request.data,
                instance=user
            )
            serializer.is_valid(raise_exception=True)
            user.set_password(serializer.validated_data.get('password'))
            user.save()
            return "Password reset."
        return self.protected_action(request, pk, 'restore', reset_password)

    def protected_action(self, request, user_id: int,
            action_type: ProtectedActions, callback) -> Response:
        """Performs an action protected by a user token.

        This is a common logic for "verify email" and "restore
        password" endpoints (actions).

        If `token` is presented in the posted data, this method tries
        to verify it and run the callback if the token is valid.
        Otherwise, it sends user an email with a new token.

        Args:
            request: Request object.
            user_id: User ID.
            action_type: Action type.
            callback: Callback to be called if the token is valid.

        Returns:
            Endpoint response.
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {'detail': "User does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
        # Verify token provided.
        if value := request.data.get('token'):
            try:
                token = UserToken.objects.get(user_id=user_id, value=value)
                if timezone.now() > token.expires_at:
                    token.delete() # It's expired anyway.
                    return Response(
                        {'detail': "Token has expired."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                # Token is valid, delete it and run the callback.
                token.delete()
                message = callback(user)
                return Response(
                    {'detail': message},
                    status=status.HTTP_200_OK
                )
            except UserToken.DoesNotExist:
                return Response(
                    {'detail': "Token does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
        # Send a new token email.
        else:
            self.send_token_email(user, action_type)
            return Response(
                {'detail': "Email sent."},
                status=status.HTTP_200_OK
            )

    @staticmethod
    def send_token_email(user: User, action_type: ProtectedActions):
        """Sends a "token" email to the given user.

        This method can send two almost identical emails:
        - With a token to verify user's email address.
        - With a token to restore user's password.

        Args:
            user: User to send email to.
            action_type: Email type.
        """
        # Ensure there is no token before generating and
        # sending a new one.
        UserToken.objects.filter(user_id=user.pk).delete()
        # Create a new token.
        token = UserToken.objects.create(user=user)
        # Do send email.
        if action_type == 'verify':
            subject = "Email verification"
        else:
            subject = "Restore password"
        send_email(
            f'user_{action_type}',
            user.email,
            params=EmailParams(subject=_(subject)),
            context={
                'token': token.value,
            })
