import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from teachkaBaseProject.tokens import account_activation_token

User = get_user_model()
password_reset_token = PasswordResetTokenGenerator()

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


@pytest.mark.django_db
class TestProfileView:
    def test_requires_login(self, client):
        response = client.get("/users/profile/")
        assert response.status_code == 302
        assert "/login" in response.url

    def test_authenticated_user_can_access(self, authenticated_client):
        response = authenticated_client.get("/users/profile/")
        assert response.status_code == 200

    def test_context_contains_user_data(self, authenticated_client, user):
        response = authenticated_client.get("/users/profile/")
        assert response.context["user_data"] == user


@pytest.mark.django_db
class TestEditProfileView:
    def test_requires_login(self, client):
        response = client.get("/users/profile/edit/")
        assert response.status_code == 302

    def test_can_update_name(self, authenticated_client, user):
        response = authenticated_client.post(
            "/users/profile/edit/",
            {
                "username": user.username,
                "first_name": "Updated",
                "last_name": "Name",
                "email": user.email,
            },
        )
        assert response.status_code == 302

        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.last_name == "Name"

    def test_username_cannot_be_changed(self, authenticated_client, user):
        original_username = user.username
        authenticated_client.post(
            "/users/profile/edit/",
            {
                "username": "hacked",
                "first_name": "Test",
                "last_name": "User",
                "email": user.email,
            },
        )
        user.refresh_from_db()
        assert user.username == original_username

    def test_duplicate_email_rejected(self, authenticated_client, user, other_user):
        response = authenticated_client.post(
            "/users/profile/edit/",
            {
                "username": user.username,
                "first_name": "Test",
                "last_name": "User",
                "email": other_user.email,
            },
        )
        assert response.status_code == 200  # re-renders form with error


@pytest.mark.django_db
class TestChangePassword:
    def test_requires_login(self, client):
        response = client.get("/users/profile/password/")
        assert response.status_code == 302

    def test_matching_email_sends_reset(self, authenticated_client, user):
        response = authenticated_client.post(
            "/users/profile/password/",
            {
                "send_to_email": user.email,
            },
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 1
        assert "/users/reset/password/" in mail.outbox[0].body

    def test_non_matching_email_no_email_sent(self, authenticated_client):
        response = authenticated_client.post(
            "/users/profile/password/",
            {
                "send_to_email": "wrong@example.com",
            },
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 0

    def test_always_shows_success_message(self, authenticated_client):
        """Same message regardless of email match — prevents enumeration."""
        response = authenticated_client.post(
            "/users/profile/password/",
            {
                "send_to_email": "wrong@example.com",
            },
            follow=True,
        )
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "password reset link" in str(messages[0]).lower()


@pytest.mark.django_db
class TestPasswordReset:
    def _build_reset_url(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)
        return f"/users/reset/password/{uid}/{token}/"

    def test_valid_link_shows_form(self, client, user):
        url = self._build_reset_url(user)
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.context

    def test_invalid_token_redirects(self, client, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        response = client.get(f"/users/reset/password/{uid}/bad-token/")
        assert response.status_code == 302

    def test_invalid_uid_redirects(self, client):
        response = client.get("/users/reset/password/bad-uid/bad-token/")
        assert response.status_code == 302

    def test_valid_reset_changes_password(self, client, user):
        url = self._build_reset_url(user)
        response = client.post(
            url,
            {
                "new_password1": "NewSecurePass456!",
                "new_password2": "NewSecurePass456!",
            },
        )
        assert response.status_code == 302

        user.refresh_from_db()
        assert user.check_password("NewSecurePass456!")

    def test_reset_redirects_to_login(self, client, user):
        url = self._build_reset_url(user)
        response = client.post(
            url,
            {
                "new_password1": "NewSecurePass456!",
                "new_password2": "NewSecurePass456!",
            },
        )
        assert response.status_code == 302
        assert "login" in response.url

    def test_token_invalidated_after_password_change(self, client, user):
        url = self._build_reset_url(user)
        client.post(
            url,
            {
                "new_password1": "NewSecurePass456!",
                "new_password2": "NewSecurePass456!",
            },
        )
        # same link should no longer work
        response = client.get(url)
        assert response.status_code == 302

    def test_mismatched_passwords_shows_form(self, client, user):
        url = self._build_reset_url(user)
        response = client.post(
            url,
            {
                "new_password1": "NewSecurePass456!",
                "new_password2": "DifferentPass789!",
            },
        )
        assert response.status_code == 200  # re-renders form with errors


@pytest.mark.django_db
class TestThemeUpdate:
    def test_requires_login(self, client):
        response = client.post("/users/theme/", {"theme": "dark"})
        assert response.status_code == 302

    def test_valid_theme_updates(self, authenticated_client, user):
        response = authenticated_client.post("/users/theme/", {"theme": "dark"})
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.theme == "dark"

    def test_invalid_theme_rejected(self, authenticated_client, user):
        response = authenticated_client.post("/users/theme/", {"theme": "neon"})
        assert response.status_code == 400
