from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserNotificationProfile


@receiver(post_save, sender=get_user_model())
def ensure_notification_profile(sender, instance, created, **kwargs):
    if created:
        UserNotificationProfile.objects.create(
            user=instance,
            notification_email=instance.email,
        )
