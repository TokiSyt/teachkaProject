import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from teachkaBaseProject.tokens import account_activation_token

User = get_user_model()

REGISTER_URL = "/register/"


@pytest.fixture
def registration_data():
    return {
        "username": "newuser",
        "first_name": "New",
        "last_name": "User",
        "email": "newuser@example.com",
        "password1": "SecurePass123!",
        "password2": "SecurePass123!",
    }


@pytest.mark.django_db
class TestRegistration:
    def test_register_creates_inactive_user(self, client, registration_data):
        response = client.post(REGISTER_URL, registration_data)
        assert response.status_code == 302

        user = User.objects.get(username="newuser")
        assert user.is_active is False
        assert user.email == "newuser@example.com"

    def test_register_sends_activation_email(self, client, registration_data):
        client.post(REGISTER_URL, registration_data)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Welcome to Teachka!"
        assert "newuser@example.com" in mail.outbox[0].to

    def test_activation_email_contains_link(self, client, registration_data):
        client.post(REGISTER_URL, registration_data)

        body = mail.outbox[0].body
        assert "/users/activate/" in body

    def test_duplicate_email_rejected(self, client, user, registration_data):
        registration_data["email"] = user.email
        response = client.post(REGISTER_URL, registration_data)
        assert response.status_code == 200

    def test_duplicate_username_rejected(self, client, user, registration_data):
        registration_data["username"] = user.username
        response = client.post(REGISTER_URL, registration_data)
        assert response.status_code == 200


@pytest.mark.django_db
class TestActivateAccount:
    def _create_inactive_user(self):
        user = User.objects.create_user(
            username="inactive",
            email="inactive@example.com",
            password="TestPass123!",
            is_active=False,
        )
        return user

    def _build_activation_url(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        return f"/users/activate/{uid}/{token}/"

    def test_valid_activation_link_activates_user(self, client):
        user = self._create_inactive_user()
        url = self._build_activation_url(user)

        response = client.get(url)
        assert response.status_code == 302

        user.refresh_from_db()
        assert user.is_active is True

    def test_valid_activation_logs_user_in(self, client):
        user = self._create_inactive_user()
        url = self._build_activation_url(user)

        client.get(url)

        response = client.get("/users/profile/")
        assert response.status_code == 200

    def test_invalid_token_does_not_activate(self, client):
        user = self._create_inactive_user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        response = client.get(f"/users/activate/{uid}/bad-token/")
        assert response.status_code == 302

        user.refresh_from_db()
        assert user.is_active is False

    def test_invalid_uid_does_not_crash(self, client):
        response = client.get("/users/activate/bad-uid/bad-token/")
        assert response.status_code == 302

    def test_token_invalidated_after_use(self, client):
        user = self._create_inactive_user()
        url = self._build_activation_url(user)

        client.get(url)
        # token should be invalid now since is_active changed
        response = client.get(url)
        assert response.status_code == 302

        # user should still be active (not deactivated)
        user.refresh_from_db()
        assert user.is_active is True
