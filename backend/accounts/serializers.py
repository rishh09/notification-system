from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import UserNotificationProfile

User = get_user_model()


class UserNotificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationProfile
        fields = ["notification_email", "whatsapp_phone", "updated_at"]
        read_only_fields = ["updated_at"]


class UserSerializer(serializers.ModelSerializer):
    notification_profile = UserNotificationProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "notification_profile",
        ]
