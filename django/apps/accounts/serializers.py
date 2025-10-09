from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from django.contrib.auth.hashers import make_password

from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""

    password = serializers.CharField(
        max_length=128,
        write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name')
        read_only_fields = ('id',)

    def validate(self, attrs):
        """Validates user password using builtin Django validators."""
        if password := attrs.get('password'):
            try:
                validate_password(password, User(**attrs))
            except ValidationError as e:
                raise serializers.ValidationError({'password': e.messages})
            # If password is OK, hash it.
            attrs['password'] = make_password(password)
        return attrs


class UserPasswordSerializer(serializers.Serializer):
    """User password serializer."""

    password = serializers.CharField(
        max_length=128,
        write_only=True)

    class Meta:
        model = User
        fields = ('password',)

    def validate_password(self, value):
        """Validates user password using builtin Django validators."""
        try:
            validate_password(value, self.instance)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class TokenSerializer(serializers.Serializer):
    """A serializer with a token field."""

    token = serializers.CharField(
        max_length=64,
        write_only=True,
        required=False)


class AccountEmailVerifySerializer(TokenSerializer):
    """Account email verification serializer."""
    pass


class AccountPasswordRestoreSerializer(TokenSerializer):
    """Account password restore serializer."""

    password = serializers.CharField(
        max_length=128,
        write_only=True,
        required=False)
