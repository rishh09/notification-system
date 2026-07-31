from django.contrib import admin

from .models import UserNotificationProfile


@admin.register(UserNotificationProfile)
class UserNotificationProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_email", "whatsapp_phone", "updated_at")
    search_fields = ("user__username", "notification_email", "whatsapp_phone")
