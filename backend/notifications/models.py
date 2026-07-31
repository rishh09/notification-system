from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class Trigger(models.Model):
    key = models.CharField(
        max_length=100,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$",
                message="Use a lowercase event key such as user.login.",
            )
        ],
        help_text="Stable website event key, for example user.login.",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class NotificationTemplate(models.Model):
    class Channel(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email"
        WEB_PUSH = "web_push", "Web Push"

    class ProviderStatus(models.TextChoices):
        NOT_SYNCED = "not_synced", "Not synced"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        NOT_APPLICABLE = "not_applicable", "Not applicable"

    trigger = models.ForeignKey(
        Trigger, on_delete=models.CASCADE, related_name="templates"
    )
    channel = models.CharField(max_length=20, choices=Channel.choices)
    subject = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField()
    is_enabled = models.BooleanField(default=True)
    variable_mapping = models.JSONField(default=dict, blank=True)
    provider_template_name = models.SlugField(max_length=512, blank=True)
    provider_language = models.CharField(max_length=20, default="en_US")
    provider_status = models.CharField(
        max_length=24,
        choices=ProviderStatus.choices,
        default=ProviderStatus.NOT_APPLICABLE,
    )
    provider_template_id = models.CharField(max_length=255, blank=True)
    provider_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["trigger__name", "channel"]
        constraints = [
            models.UniqueConstraint(
                fields=["trigger", "channel"],
                name="unique_template_per_trigger_channel",
            )
        ]

    def clean(self):
        errors = {}
        if self.channel == self.Channel.EMAIL and not self.subject.strip():
            errors["subject"] = "Email templates require a subject."
        if self.channel == self.Channel.WEB_PUSH and not self.title.strip():
            errors["title"] = "Web Push templates require a title."
        if self.channel == self.Channel.WHATSAPP:
            if self.provider_status == self.ProviderStatus.NOT_APPLICABLE:
                self.provider_status = self.ProviderStatus.NOT_SYNCED
        elif self.provider_status == self.ProviderStatus.NOT_SYNCED:
            self.provider_status = self.ProviderStatus.NOT_APPLICABLE
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trigger.name} - {self.get_channel_display()}"


class PushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    subscription_id = models.CharField(max_length=255, unique=True)
    device_label = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user} - {self.device_label or self.subscription_id}"


class NotificationDelivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    trigger = models.ForeignKey(
        Trigger, on_delete=models.CASCADE, related_name="deliveries"
    )
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_deliveries",
    )
    channel = models.CharField(max_length=20, choices=NotificationTemplate.Channel.choices)
    recipient = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    provider_message_id = models.CharField(max_length=255, blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    rendered_content = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.trigger.key} / {self.channel} / {self.status}"
