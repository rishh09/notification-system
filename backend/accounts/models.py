from django.conf import settings
from django.db import models


class UserNotificationProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_profile",
    )
    notification_email = models.EmailField(blank=True)
    whatsapp_phone = models.CharField(
        max_length=32,
        blank=True,
        help_text="International format, for example 919876543210.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification profile for {self.user}"
