from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from unittest.mock import patch

from .models import (
    NotificationDelivery,
    NotificationTemplate,
    PushSubscription,
    Trigger,
)
from .services.dispatch import dispatch_notification
from .services.providers import ProviderError, send_whatsapp, sync_whatsapp_template
from .services.rendering import render_notification

User = get_user_model()


def create_trigger_with_templates(key="user.login", name="Login"):
    trigger = Trigger.objects.create(key=key, name=name)
    common = {
        "trigger": trigger,
        "is_enabled": True,
        "variable_mapping": {"user_name": "user.first_name"},
    }
    NotificationTemplate.objects.create(
        **common,
        channel=NotificationTemplate.Channel.WHATSAPP,
        body="Welcome {{user_name}}",
        provider_template_name=key.replace(".", "_"),
    )
    NotificationTemplate.objects.create(
        **common,
        channel=NotificationTemplate.Channel.EMAIL,
        subject="Hello {{user_name}}",
        body="Welcome {{user_name}}",
    )
    NotificationTemplate.objects.create(
        **common,
        channel=NotificationTemplate.Channel.WEB_PUSH,
        title="Welcome",
        body="Hello {{user_name}}",
    )
    return trigger


@override_settings(NOTIFICATION_PROVIDER_MODE="mock")
class NotificationDomainTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="demo",
            password="UserPass123!",
            first_name="Demo",
            email="demo@example.com",
        )
        self.user.notification_profile.whatsapp_phone = "919876543210"
        self.user.notification_profile.save()
        PushSubscription.objects.create(
            user=self.user,
            subscription_id="test-subscription",
            device_label="Test browser",
        )
        self.trigger = create_trigger_with_templates()

    def test_variable_mapping_renders_all_fields(self):
        template = self.trigger.templates.get(
            channel=NotificationTemplate.Channel.EMAIL
        )
        rendered = render_notification(template, {"user": self.user})
        self.assertEqual(rendered.subject, "Hello Demo")
        self.assertEqual(rendered.body, "Welcome Demo")

    def test_dispatch_sends_all_three_channels(self):
        deliveries = dispatch_notification(
            "user.login",
            user=self.user,
            context={"user": self.user},
        )
        self.assertEqual(len(deliveries), 3)
        self.assertEqual(
            {delivery.channel for delivery in deliveries},
            {"whatsapp", "email", "web_push"},
        )
        self.assertTrue(
            all(
                delivery.status == NotificationDelivery.Status.SENT
                for delivery in deliveries
            )
        )

    def test_disabled_template_is_not_dispatched(self):
        template = self.trigger.templates.get(
            channel=NotificationTemplate.Channel.WHATSAPP
        )
        template.is_enabled = False
        template.save()
        deliveries = dispatch_notification(
            "user.login",
            user=self.user,
            context={"user": self.user},
        )
        self.assertEqual(len(deliveries), 2)
        self.assertNotIn("whatsapp", {item.channel for item in deliveries})


class TwilioWhatsAppProviderTests(TestCase):
    def setUp(self):
        self.trigger = Trigger.objects.create(key="user.login", name="Login")
        self.template = NotificationTemplate.objects.create(
            trigger=self.trigger,
            channel=NotificationTemplate.Channel.WHATSAPP,
            body="Welcome {{user_name}}",
            variable_mapping={"user_name": "user.first_name"},
            provider_template_name="user_login",
        )
        self.rendered = render_notification(
            self.template, {"user_name": "Asif"}
        )

    @override_settings(
        NOTIFICATION_PROVIDER_MODE="live",
        WHATSAPP_PROVIDER="twilio",
        TWILIO_ACCOUNT_SID="ACtest",
        TWILIO_AUTH_TOKEN="secret",
        TWILIO_WHATSAPP_FROM="whatsapp:+17372508034",
        TWILIO_WHATSAPP_CONTENT_SID="",
    )
    @patch("notifications.services.providers._request_form")
    def test_twilio_sandbox_sends_rendered_whatsapp_body(self, request_form):
        request_form.return_value = {"sid": "SM123", "status": "queued"}

        result = send_whatsapp(
            self.template,
            "919876543210",
            self.rendered,
        )

        self.assertEqual(result.message_id, "SM123")
        request_form.assert_called_once_with(
            "https://api.twilio.com/2010-04-01/Accounts/ACtest/Messages.json",
            username="ACtest",
            password="secret",
            payload={
                "From": "whatsapp:+17372508034",
                "To": "whatsapp:+919876543210",
                "Body": "Welcome Asif",
            },
        )

    @override_settings(
        NOTIFICATION_PROVIDER_MODE="live",
        WHATSAPP_PROVIDER="twilio",
        TWILIO_ACCOUNT_SID="ACtest",
        TWILIO_AUTH_TOKEN="secret",
        TWILIO_WHATSAPP_FROM="whatsapp:+17372508034",
        TWILIO_WHATSAPP_CONTENT_SID="HXtrial",
    )
    @patch("notifications.services.providers._request_form")
    def test_twilio_trial_uses_account_content_sid(self, request_form):
        request_form.return_value = {"sid": "SM456", "status": "queued"}

        result = send_whatsapp(
            self.template,
            "919876543210",
            self.rendered,
        )

        self.assertEqual(result.message_id, "SM456")
        request_form.assert_called_once_with(
            "https://api.twilio.com/2010-04-01/Accounts/ACtest/Messages.json",
            username="ACtest",
            password="secret",
            payload={
                "From": "whatsapp:+17372508034",
                "To": "whatsapp:+919876543210",
                "ContentSid": "HXtrial",
            },
        )

    @override_settings(
        NOTIFICATION_PROVIDER_MODE="live",
        WHATSAPP_PROVIDER="twilio",
        TWILIO_ACCOUNT_SID="",
        TWILIO_AUTH_TOKEN="",
        TWILIO_WHATSAPP_FROM="",
    )
    def test_twilio_sandbox_requires_credentials(self):
        with self.assertRaisesMessage(
            ProviderError,
            "Twilio WhatsApp Sandbox credentials are not configured.",
        ):
            send_whatsapp(self.template, "919876543210", self.rendered)

    @override_settings(
        NOTIFICATION_PROVIDER_MODE="live",
        WHATSAPP_PROVIDER="twilio",
    )
    def test_twilio_sandbox_does_not_claim_meta_template_sync(self):
        with self.assertRaisesMessage(
            ProviderError,
            "Custom WhatsApp template synchronization requires the Meta provider.",
        ):
            sync_whatsapp_template(self.template)


@override_settings(NOTIFICATION_PROVIDER_MODE="mock")
class NotificationApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin",
            password="AdminPass123!",
            email="admin@example.com",
            first_name="Admin",
        )
        self.admin.notification_profile.whatsapp_phone = "919999999999"
        self.admin.notification_profile.save()
        PushSubscription.objects.create(
            user=self.admin,
            subscription_id="admin-browser",
        )
        self.user = User.objects.create_user(
            username="demo",
            password="UserPass123!",
            email="demo@example.com",
            first_name="Demo",
        )
        self.user.notification_profile.whatsapp_phone = "919876543210"
        self.user.notification_profile.save()
        PushSubscription.objects.create(
            user=self.user,
            subscription_id="demo-browser",
        )
        self.login_trigger = create_trigger_with_templates()
        self.logout_trigger = create_trigger_with_templates("user.logout", "Logout")
        self.client = APIClient()

    def test_non_admin_cannot_manage_triggers(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/admin/triggers/")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_trigger_matrix(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/admin/triggers/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(len(response.data[0]["templates"]), 3)

    def test_user_can_refresh_an_existing_push_subscription(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/push/subscriptions/",
            {
                "subscription_id": "demo-browser",
                "device_label": "Refreshed browser",
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            PushSubscription.objects.filter(subscription_id="demo-browser").count(),
            1,
        )
        subscription = PushSubscription.objects.get(subscription_id="demo-browser")
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.device_label, "Refreshed browser")
        self.assertTrue(subscription.is_active)

    def test_admin_can_create_edit_and_delete_trigger_and_template(self):
        self.client.force_authenticate(self.admin)
        create_trigger = self.client.post(
            "/api/admin/triggers/",
            {
                "key": "user.password_reset",
                "name": "Password reset",
                "description": "Fires when a password reset is requested.",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(create_trigger.status_code, 201)

        create_template = self.client.post(
            "/api/admin/templates/",
            {
                "trigger": create_trigger.data["id"],
                "channel": "email",
                "subject": "Reset requested",
                "body": "Hi {{user_name}}, a reset was requested.",
                "variable_mapping": {"user_name": "user.first_name"},
                "is_enabled": True,
            },
            format="json",
        )
        self.assertEqual(create_template.status_code, 201)

        edit_template = self.client.patch(
            f"/api/admin/templates/{create_template.data['id']}/",
            {"body": "Updated for {{user_name}}."},
            format="json",
        )
        self.assertEqual(edit_template.status_code, 200)
        self.assertEqual(edit_template.data["body"], "Updated for {{user_name}}.")

        delete_trigger = self.client.delete(
            f"/api/admin/triggers/{create_trigger.data['id']}/"
        )
        self.assertEqual(delete_trigger.status_code, 204)
        self.assertFalse(
            NotificationTemplate.objects.filter(
                pk=create_template.data["id"]
            ).exists()
        )

    def test_admin_can_toggle_and_test_template(self):
        self.client.force_authenticate(self.admin)
        template = self.login_trigger.templates.get(
            channel=NotificationTemplate.Channel.EMAIL
        )
        toggle = self.client.post(
            f"/api/admin/templates/{template.pk}/toggle/",
            {"is_enabled": False},
            format="json",
        )
        self.assertEqual(toggle.status_code, 200)
        self.assertFalse(toggle.data["is_enabled"])

        test_send = self.client.post(
            f"/api/admin/templates/{template.pk}/test-send/",
            {
                "destination": "admin@example.com",
                "variables": {"user_name": "Asif"},
            },
            format="json",
        )
        self.assertEqual(test_send.status_code, 200)
        self.assertEqual(test_send.data[0]["status"], "sent")
        self.assertEqual(
            test_send.data[0]["rendered_content"]["subject"], "Hello Asif"
        )

    def test_missing_recipient_is_recorded_as_skipped(self):
        self.client.force_authenticate(self.admin)
        self.admin.notification_profile.whatsapp_phone = ""
        self.admin.notification_profile.save()
        template = self.login_trigger.templates.get(
            channel=NotificationTemplate.Channel.WHATSAPP
        )
        response = self.client.post(
            f"/api/admin/templates/{template.pk}/test-send/",
            {"variables": {"user_name": "Admin"}},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["status"], "skipped")
        self.assertIn("No recipient", response.data[0]["error_message"])

    def test_login_and_logout_fire_real_triggers(self):
        login = self.client.post(
            "/api/auth/login/",
            {"username": "demo", "password": "UserPass123!"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn("token", login.data)
        self.assertEqual(
            NotificationDelivery.objects.filter(
                trigger=self.login_trigger, user=self.user
            ).count(),
            3,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['token']}")
        logout = self.client.post("/api/auth/logout/", {}, format="json")
        self.assertEqual(logout.status_code, 204)
        self.assertFalse(Token.objects.filter(user=self.user).exists())
        self.assertEqual(
            NotificationDelivery.objects.filter(
                trigger=self.logout_trigger, user=self.user
            ).count(),
            3,
        )
