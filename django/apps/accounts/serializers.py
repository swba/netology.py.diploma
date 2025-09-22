from rest_framework import serializers
from django.contrib.auth.hashers import make_password

from apps.accounts.models import User


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')

    # noinspection PyMethodMayBeStatic
    def validate_password(self, value: str) -> str:
        return make_password(value)
