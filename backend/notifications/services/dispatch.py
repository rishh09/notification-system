from typing import Any

from django.contrib.auth import get_user_model

from notifications.models import (
    NotificationDelivery,
    NotificationTemplate,
    PushSubscription,
    Trigger,
)

from .providers import ProviderError, send_email, send_web_push, send_whatsapp
from .rendering import render_notification

User = get_user_model()


def _destinations_for(
    template: NotificationTemplate,
    user: User,
) -> list[str]:
    profile = user.notification_profile
    if template.channel == NotificationTemplate.Channel.EMAIL:
        destination = profile.notification_email or user.email
        return [destination] if destination else []
    if template.channel == NotificationTemplate.Channel.WHATSAPP:
        return [profile.whatsapp_phone] if profile.whatsapp_phone else []
    return list(
        PushSubscription.objects.filter(user=user, is_active=True).values_list(
            "subscription_id", flat=True
        )
    )


def _send(
    template: NotificationTemplate,
    recipient: str,
    rendered,
):
    if template.channel == NotificationTemplate.Channel.WHATSAPP:
        return send_whatsapp(template, recipient, rendered)
    if template.channel == NotificationTemplate.Channel.EMAIL:
        return send_email(recipient, rendered)
    return send_web_push(recipient, rendered)


def deliver_template(
    template: NotificationTemplate,
    *,
    user: User,
    context: dict[str, Any],
    destinations: list[str] | None = None,
) -> list[NotificationDelivery]:
    rendered = render_notification(template, context)
    recipients = destinations if destinations is not None else _destinations_for(template, user)
    if not recipients:
        return [
            NotificationDelivery.objects.create(
                trigger=template.trigger,
                template=template,
                user=user,
                channel=template.channel,
                status=NotificationDelivery.Status.SKIPPED,
                error_message="No recipient is configured for this channel.",
                rendered_content=rendered.as_dict(),
            )
        ]

    deliveries: list[NotificationDelivery] = []
    for recipient in recipients:
        delivery = NotificationDelivery.objects.create(
            trigger=template.trigger,
            template=template,
            user=user,
            channel=template.channel,
            recipient=recipient,
            rendered_content=rendered.as_dict(),
        )
        try:
            result = _send(template, recipient, rendered)
            delivery.status = NotificationDelivery.Status.SENT
            delivery.provider_message_id = result.message_id
            delivery.provider_response = result.response
        except ProviderError as exc:
            delivery.status = NotificationDelivery.Status.FAILED
            delivery.error_message = str(exc)
        except Exception as exc:
            delivery.status = NotificationDelivery.Status.FAILED
            delivery.error_message = f"Unexpected provider error: {exc}"
        delivery.save(
            update_fields=[
                "status",
                "provider_message_id",
                "provider_response",
                "error_message",
            ]
        )
        deliveries.append(delivery)
    return deliveries


def dispatch_notification(
    trigger_key: str,
    *,
    user: User,
    context: dict[str, Any] | None = None,
) -> list[NotificationDelivery]:
    try:
        trigger = Trigger.objects.prefetch_related("templates").get(
            key=trigger_key, is_active=True
        )
    except Trigger.DoesNotExist:
        return []

    full_context = {"user": user, **(context or {})}
    deliveries: list[NotificationDelivery] = []
    for template in trigger.templates.filter(is_enabled=True):
        deliveries.extend(
            deliver_template(template, user=user, context=full_context)
        )
    return deliveries


def send_test_notification(
    template: NotificationTemplate,
    *,
    user: User,
    destination: str | None,
    variables: dict[str, Any] | None,
) -> list[NotificationDelivery]:
    context: dict[str, Any] = {
        "user": user,
        "user_name": user.first_name or user.username,
        **(variables or {}),
    }
    destinations = [destination] if destination else None
    return deliver_template(
        template,
        user=user,
        context=context,
        destinations=destinations,
    )
