from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import (
    NotificationDelivery,
    NotificationTemplate,
    PushSubscription,
    Trigger,
)
from .serializers import (
    NotificationDeliverySerializer,
    NotificationTemplateSerializer,
    PushSubscriptionSerializer,
    TriggerSerializer,
)
from .services.dispatch import send_test_notification
from .services.providers import (
    ProviderError,
    fetch_whatsapp_template_status,
    sync_whatsapp_template,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


class TriggerViewSet(viewsets.ModelViewSet):
    queryset = Trigger.objects.prefetch_related("templates").all()
    serializer_class = TriggerSerializer
    permission_classes = [IsAdminUser]


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.select_related("trigger").all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        template = self.get_object()
        requested = request.data.get("is_enabled")
        template.is_enabled = not template.is_enabled if requested is None else bool(requested)
        template.save(update_fields=["is_enabled", "updated_at"])
        return Response(self.get_serializer(template).data)

    @action(detail=True, methods=["post"], url_path="test-send")
    def test_send(self, request, pk=None):
        template = self.get_object()
        variables = request.data.get("variables", {})
        if not isinstance(variables, dict):
            return Response(
                {"variables": "Variables must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        deliveries = send_test_notification(
            template,
            user=request.user,
            destination=request.data.get("destination") or None,
            variables=variables,
        )
        return Response(NotificationDeliverySerializer(deliveries, many=True).data)

    @action(detail=True, methods=["post"], url_path="whatsapp-sync")
    def whatsapp_sync(self, request, pk=None):
        template = self.get_object()
        try:
            response = sync_whatsapp_template(template)
        except ProviderError as exc:
            template.provider_status = NotificationTemplate.ProviderStatus.REJECTED
            template.provider_error = str(exc)
            template.save(
                update_fields=["provider_status", "provider_error", "updated_at"]
            )
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        template.provider_template_id = str(response.get("id", ""))
        raw_status = str(response.get("status", "PENDING")).lower()
        allowed = {
            value for value, _ in NotificationTemplate.ProviderStatus.choices
        }
        template.provider_status = (
            raw_status
            if raw_status in allowed
            else NotificationTemplate.ProviderStatus.PENDING
        )
        template.provider_error = ""
        template.save(
            update_fields=[
                "provider_template_id",
                "provider_status",
                "provider_error",
                "updated_at",
            ]
        )
        return Response(
            {"template": self.get_serializer(template).data, "provider": response}
        )

    @action(detail=True, methods=["get"], url_path="whatsapp-status")
    def whatsapp_status(self, request, pk=None):
        template = self.get_object()
        try:
            response = fetch_whatsapp_template_status(template)
        except ProviderError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        matches = response.get("data", [])
        if matches:
            match = matches[0]
            raw_status = str(match.get("status", "PENDING")).lower()
            allowed = {
                value for value, _ in NotificationTemplate.ProviderStatus.choices
            }
            template.provider_status = (
                raw_status
                if raw_status in allowed
                else NotificationTemplate.ProviderStatus.PENDING
            )
            template.provider_template_id = str(
                match.get("id", template.provider_template_id)
            )
            template.provider_error = ""
            template.save(
                update_fields=[
                    "provider_status",
                    "provider_template_id",
                    "provider_error",
                    "updated_at",
                ]
            )
        return Response(
            {"template": self.get_serializer(template).data, "provider": response}
        )


class PushSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = PushSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PushSubscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        subscription_id = serializer.validated_data["subscription_id"]
        device_label = serializer.validated_data.get("device_label", "")
        defaults = {
            "device_label": device_label,
            "is_active": serializer.validated_data.get("is_active", True),
        }
        if device_label:
            PushSubscription.objects.filter(
                user=self.request.user,
                device_label=device_label,
            ).exclude(subscription_id=subscription_id).update(is_active=False)
        instance, _ = PushSubscription.objects.update_or_create(
            subscription_id=subscription_id,
            defaults={"user": self.request.user, **defaults},
        )
        serializer.instance = instance


class NotificationDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NotificationDelivery.objects.select_related(
        "trigger", "template", "user"
    ).all()
    serializer_class = NotificationDeliverySerializer
    permission_classes = [IsAdminUser]
