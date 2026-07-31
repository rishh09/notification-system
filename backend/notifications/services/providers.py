import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any

from django.conf import settings

from notifications.models import NotificationTemplate

from .rendering import RenderedNotification


class ProviderError(RuntimeError):
    pass


@dataclass
class ProviderResult:
    message_id: str
    response: dict[str, Any]


def _mock_result(channel: str, recipient: str) -> ProviderResult:
    message_id = f"mock-{channel}-{uuid.uuid4()}"
    return ProviderResult(
        message_id=message_id,
        response={"mock": True, "channel": channel, "recipient": recipient},
    )


def _request_json(
    url: str,
    *,
    method: str = "POST",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(f"Provider returned HTTP {exc.code}: {raw}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"Provider request failed: {exc.reason}") from exc


def _request_form(
    url: str,
    *,
    username: str,
    password: str,
    payload: dict[str, str],
) -> dict[str, Any]:
    credentials = base64.b64encode(
        f"{username}:{password}".encode("utf-8")
    ).decode("ascii")
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/json",
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(f"Provider returned HTTP {exc.code}: {raw}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"Provider request failed: {exc.reason}") from exc


def _twilio_whatsapp_address(phone_number: str) -> str:
    value = phone_number.strip()
    if value.startswith("whatsapp:"):
        return value
    if not value.startswith("+"):
        value = f"+{value}"
    return f"whatsapp:{value}"


def _send_whatsapp_with_twilio(
    recipient: str,
    rendered: RenderedNotification,
) -> ProviderResult:
    if (
        not settings.TWILIO_ACCOUNT_SID
        or not settings.TWILIO_AUTH_TOKEN
        or not settings.TWILIO_WHATSAPP_FROM
    ):
        raise ProviderError("Twilio WhatsApp Sandbox credentials are not configured.")

    payload = {
        "From": _twilio_whatsapp_address(settings.TWILIO_WHATSAPP_FROM),
        "To": _twilio_whatsapp_address(recipient),
    }
    if settings.TWILIO_WHATSAPP_CONTENT_SID:
        payload["ContentSid"] = settings.TWILIO_WHATSAPP_CONTENT_SID
    else:
        payload["Body"] = rendered.body

    response = _request_form(
        (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{settings.TWILIO_ACCOUNT_SID}/Messages.json"
        ),
        username=settings.TWILIO_ACCOUNT_SID,
        password=settings.TWILIO_AUTH_TOKEN,
        payload=payload,
    )
    if response.get("error_code"):
        raise ProviderError(response.get("message", "Twilio rejected the message."))
    return ProviderResult(message_id=response.get("sid", ""), response=response)


def send_whatsapp(
    template: NotificationTemplate,
    recipient: str,
    rendered: RenderedNotification,
) -> ProviderResult:
    if settings.NOTIFICATION_PROVIDER_MODE == "mock":
        return _mock_result("whatsapp", recipient)
    if settings.WHATSAPP_PROVIDER == "twilio":
        return _send_whatsapp_with_twilio(recipient, rendered)
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise ProviderError("WhatsApp credentials are not configured.")
    if not template.provider_template_name:
        raise ProviderError("The WhatsApp provider template name is missing.")

    components = []
    if rendered.variables:
        components.append(
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": value}
                    for value in rendered.variables.values()
                ],
            }
        )
    payload: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template.provider_template_name,
            "language": {"code": template.provider_language},
        },
    }
    if components:
        payload["template"]["components"] = components

    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    response = _request_json(
        url,
        headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"},
        payload=payload,
    )
    messages = response.get("messages", [])
    message_id = messages[0].get("id", "") if messages else ""
    return ProviderResult(message_id=message_id, response=response)


def send_email(
    recipient: str,
    rendered: RenderedNotification,
) -> ProviderResult:
    if settings.NOTIFICATION_PROVIDER_MODE == "mock":
        return _mock_result("email", recipient)
    if not settings.POSTMARKAPP_TOKEN or not settings.POSTMARK_FROM_EMAIL:
        raise ProviderError("Postmark credentials are not configured.")

    response = _request_json(
        "https://api.postmarkapp.com/email",
        headers={"X-Postmark-Server-Token": settings.POSTMARKAPP_TOKEN},
        payload={
            "From": settings.POSTMARK_FROM_EMAIL,
            "To": recipient,
            "Subject": rendered.subject,
            "TextBody": rendered.body,
            "MessageStream": "outbound",
        },
    )
    if response.get("ErrorCode", 0) != 0:
        raise ProviderError(response.get("Message", "Postmark rejected the message."))
    return ProviderResult(
        message_id=response.get("MessageID", ""),
        response=response,
    )


def send_web_push(
    subscription_id: str,
    rendered: RenderedNotification,
) -> ProviderResult:
    if settings.NOTIFICATION_PROVIDER_MODE == "mock":
        return _mock_result("web_push", subscription_id)
    if not settings.ONESIGNAL_APP_ID or not settings.ONESIGNAL_REST_API_KEY:
        raise ProviderError("OneSignal credentials are not configured.")

    response = _request_json(
        "https://api.onesignal.com/notifications",
        headers={"Authorization": f"Key {settings.ONESIGNAL_REST_API_KEY}"},
        payload={
            "app_id": settings.ONESIGNAL_APP_ID,
            "include_subscription_ids": [subscription_id],
            "target_channel": "push",
            "headings": {"en": rendered.title},
            "contents": {"en": rendered.body},
            "url": settings.FRONTEND_URL,
        },
    )
    if response.get("errors"):
        raise ProviderError(json.dumps(response["errors"]))
    return ProviderResult(message_id=response.get("id", ""), response=response)


def _provider_body(template: NotificationTemplate) -> tuple[str, list[str]]:
    names: list[str] = []

    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in names:
            names.append(name)
        return f"{{{{{names.index(name) + 1}}}}}"

    body = re.sub(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}", replace, template.body)
    return body, names


def sync_whatsapp_template(template: NotificationTemplate) -> dict[str, Any]:
    if template.channel != NotificationTemplate.Channel.WHATSAPP:
        raise ProviderError("Only WhatsApp templates can be synchronized.")
    if settings.NOTIFICATION_PROVIDER_MODE == "mock":
        return {
            "id": f"mock-template-{template.pk}",
            "status": "PENDING",
            "mock": True,
        }
    if settings.WHATSAPP_PROVIDER == "twilio":
        raise ProviderError(
            "Custom WhatsApp template synchronization requires the Meta provider."
        )
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_BUSINESS_ACCOUNT_ID:
        raise ProviderError("WhatsApp template-management credentials are not configured.")
    if not template.provider_template_name:
        raise ProviderError("A provider template name is required.")

    body, variable_names = _provider_body(template)
    body_component: dict[str, Any] = {"type": "BODY", "text": body}
    if variable_names:
        body_component["example"] = {
            "body_text": [[f"Sample {name.replace('_', ' ')}" for name in variable_names]]
        }

    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_API_VERSION}/"
        f"{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"
    )
    return _request_json(
        url,
        headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"},
        payload={
            "name": template.provider_template_name,
            "language": template.provider_language,
            "category": "UTILITY",
            "components": [body_component],
        },
    )


def fetch_whatsapp_template_status(
    template: NotificationTemplate,
) -> dict[str, Any]:
    if settings.NOTIFICATION_PROVIDER_MODE == "mock":
        return {
            "data": [
                {
                    "id": template.provider_template_id or f"mock-template-{template.pk}",
                    "name": template.provider_template_name,
                    "status": "APPROVED",
                }
            ],
            "mock": True,
        }
    if settings.WHATSAPP_PROVIDER == "twilio":
        raise ProviderError(
            "WhatsApp template status checks require the Meta provider."
        )
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_BUSINESS_ACCOUNT_ID:
        raise ProviderError("WhatsApp template-management credentials are not configured.")

    query = urllib.parse.urlencode(
        {"name": template.provider_template_name, "limit": 10}
    )
    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_API_VERSION}/"
        f"{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates?{query}"
    )
    return _request_json(
        url,
        method="GET",
        headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"},
    )
