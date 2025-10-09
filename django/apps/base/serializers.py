from rest_framework import serializers


class BaseResponseSerializer(serializers.Serializer):
    """Base response serializer containing one `detail` field."""

    detail = serializers.CharField(
        read_only=True,
        help_text="Response detail.")
