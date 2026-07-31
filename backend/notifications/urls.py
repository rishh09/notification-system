from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    NotificationDeliveryViewSet,
    NotificationTemplateViewSet,
    PushSubscriptionViewSet,
    TriggerViewSet,
    health,
)

router = DefaultRouter()
router.register("admin/triggers", TriggerViewSet, basename="trigger")
router.register(
    "admin/templates", NotificationTemplateViewSet, basename="notification-template"
)
router.register(
    "admin/deliveries", NotificationDeliveryViewSet, basename="notification-delivery"
)
router.register(
    "push/subscriptions", PushSubscriptionViewSet, basename="push-subscription"
)

urlpatterns = [
    path("health/", health, name="health"),
    path("", include(router.urls)),
]
