from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserNotificationProfileTests(TestCase):
    def test_profile_is_created_with_user_email(self):
        user = User.objects.create_user(
            username="profile-test",
            email="profile@example.com",
            password="SafePassword123!",
        )
        self.assertEqual(
            user.notification_profile.notification_email,
            "profile@example.com",
        )
