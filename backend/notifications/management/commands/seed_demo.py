import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from notifications.models import NotificationTemplate, Trigger

User = get_user_model()


class Command(BaseCommand):
    help = "Create local demo users, triggers, and channel templates."

    def handle(self, *args, **options):
        admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "AdminPass123!")
        user_password = os.getenv("DEMO_USER_PASSWORD", "UserPass123!")

        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(admin_password)
        admin.save()

        user, _ = User.objects.get_or_create(
            username="demo",
            defaults={
                "email": "demo@example.com",
                "first_name": "Demo",
            },
        )
        user.set_password(user_password)
        user.save()

        triggers = [
            ("user.login", "Login", "Fires after a successful website login."),
            ("user.logout", "Logout", "Fires when a user signs out."),
        ]
        messages = {
            "user.login": {
                "whatsapp": ("", "", "Welcome back, {{user_name}}!"),
                "email": (
                    "You logged in successfully",
                    "",
                    "Hi {{user_name}}, you have logged in successfully.",
                ),
                "web_push": (
                    "",
                    "Welcome back",
                    "Hi {{user_name}}, your login was successful.",
                ),
            },
            "user.logout": {
                "whatsapp": ("", "", "See you soon, {{user_name}}!"),
                "email": (
                    "You have logged out",
                    "",
                    "Hi {{user_name}}, you have safely logged out.",
                ),
                "web_push": (
                    "",
                    "Signed out",
                    "See you next time, {{user_name}}.",
                ),
            },
        }

        for key, name, description in triggers:
            trigger, _ = Trigger.objects.update_or_create(
                key=key,
                defaults={
                    "name": name,
                    "description": description,
                    "is_active": True,
                },
            )
            for channel, (subject, title, body) in messages[key].items():
                defaults = {
                    "subject": subject,
                    "title": title,
                    "body": body,
                    "is_enabled": True,
                    "variable_mapping": {"user_name": "user.first_name"},
                }
                if channel == NotificationTemplate.Channel.WHATSAPP:
                    defaults.update(
                        {
                            "provider_template_name": key.replace(".", "_"),
                            "provider_status": NotificationTemplate.ProviderStatus.NOT_SYNCED,
                        }
                    )
                NotificationTemplate.objects.update_or_create(
                    trigger=trigger,
                    channel=channel,
                    defaults=defaults,
                )

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write("Admin username: admin")
        self.stdout.write("Demo username: demo")
        self.stdout.write("Passwords come from DEMO_ADMIN_PASSWORD and DEMO_USER_PASSWORD.")
