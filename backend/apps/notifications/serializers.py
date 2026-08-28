from __future__ import annotations

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "company",
            "user",
            "type",
            "title",
            "body",
            "severity",
            "read_at",
            "metadata",
            "created_at",
            "updated_at",
        ]


class NotificationMarkReadSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    all = serializers.BooleanField(required=False, default=False)