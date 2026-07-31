from django.contrib import admin

from .models import (
    NotificationDelivery,
    NotificationTemplate,
    PushSubscription,
    Trigger,
)


class NotificationTemplateInline(admin.TabularInline):
    model = NotificationTemplate
    extra = 0


@admin.register(Trigger)
class TriggerAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "key")
    inlines = [NotificationTemplateInline]


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "trigger",
        "channel",
        "is_enabled",
        "provider_status",
        "updated_at",
    )
    list_filter = ("channel", "is_enabled", "provider_status")
    search_fields = ("trigger__name", "subject", "title", "body")


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "device_label", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("user__username", "subscription_id", "device_label")


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ("trigger", "channel", "recipient", "status", "created_at")
    list_filter = ("channel", "status")
    search_fields = ("recipient", "provider_message_id", "error_message")
    readonly_fields = (
        "trigger",
        "template",
        "user",
        "channel",
        "recipient",
        "status",
        "provider_message_id",
        "provider_response",
        "error_message",
        "rendered_content",
        "created_at",
    )
