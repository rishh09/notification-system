from rest_framework import serializers

from .models import (
    NotificationDelivery,
    NotificationTemplate,
    PushSubscription,
    Trigger,
)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    channel_label = serializers.CharField(source="get_channel_display", read_only=True)
    provider_status_label = serializers.CharField(
        source="get_provider_status_display", read_only=True
    )

    class Meta:
        model = NotificationTemplate
        fields = [
            "id",
            "trigger",
            "channel",
            "channel_label",
            "subject",
            "title",
            "body",
            "is_enabled",
            "variable_mapping",
            "provider_template_name",
            "provider_language",
            "provider_status",
            "provider_status_label",
            "provider_template_id",
            "provider_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "provider_status",
            "provider_status_label",
            "provider_template_id",
            "provider_error",
            "created_at",
            "updated_at",
        ]

    def validate_variable_mapping(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Variable mappings must be a JSON object.")
        if any(not isinstance(key, str) or not isinstance(path, str) for key, path in value.items()):
            raise serializers.ValidationError("Variable names and paths must be strings.")
        return value

    def validate(self, attrs):
        channel = attrs.get("channel", getattr(self.instance, "channel", None))
        subject = attrs.get("subject", getattr(self.instance, "subject", ""))
        title = attrs.get("title", getattr(self.instance, "title", ""))
        body = attrs.get("body", getattr(self.instance, "body", ""))
        errors = {}
        if not body or not body.strip():
            errors["body"] = "A message body is required."
        if channel == NotificationTemplate.Channel.EMAIL and not subject.strip():
            errors["subject"] = "Email templates require a subject."
        if channel == NotificationTemplate.Channel.WEB_PUSH and not title.strip():
            errors["title"] = "Web Push templates require a title."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class TriggerSerializer(serializers.ModelSerializer):
    templates = NotificationTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = Trigger
        fields = [
            "id",
            "key",
            "name",
            "description",
            "is_active",
            "templates",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = [
            "id",
            "subscription_id",
            "device_label",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"subscription_id": {"validators": []}}


class NotificationDeliverySerializer(serializers.ModelSerializer):
    trigger_name = serializers.CharField(source="trigger.name", read_only=True)
    channel_label = serializers.CharField(source="get_channel_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = NotificationDelivery
        fields = [
            "id",
            "trigger",
            "trigger_name",
            "template",
            "user",
            "channel",
            "channel_label",
            "recipient",
            "status",
            "status_label",
            "provider_message_id",
            "provider_response",
            "error_message",
            "rendered_content",
            "created_at",
        ]
