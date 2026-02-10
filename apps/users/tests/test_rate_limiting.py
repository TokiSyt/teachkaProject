from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(AXES_ENABLED=True)
class TestRateLimiting(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.url = reverse("login")

    def test_lockout_after_failed_attempts(self):
        for _ in range(5):
            self.client.post(self.url, {"username": self.user.username, "password": "wrong"})

        response = self.client.post(self.url, {"username": self.user.username, "password": "wrong"})
        assert response.status_code == 429

    def test_successful_login_after_failures(self):
        for _ in range(3):
            self.client.post(self.url, {"username": self.user.username, "password": "wrong"})

        response = self.client.post(self.url, {"username": self.user.username, "password": "testpass123"})
        assert response.status_code == 302

    def test_lockout_blocks_correct_password(self):
        for _ in range(5):
            self.client.post(self.url, {"username": self.user.username, "password": "wrong"})

        response = self.client.post(self.url, {"username": self.user.username, "password": "testpass123"})
        assert response.status_code == 429
