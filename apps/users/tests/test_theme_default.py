"""Tests for the Palette (fantasy) theme being the default."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestThemeDefault:
    """The model default and rendered fallbacks should be 'fantasy'."""

    def test_new_user_defaults_to_fantasy(self):
        u = User.objects.create_user(username="newbie", email="n@e.com", password="x")
        assert u.theme == "fantasy"

    def test_default_persists_after_reload(self):
        u = User.objects.create_user(username="newbie2", email="n2@e.com", password="x")
        u.refresh_from_db()
        assert u.theme == "fantasy"

    def test_explicit_theme_overrides_default(self):
        u = User.objects.create_user(username="lighty", email="l@e.com", password="x", theme="light")
        assert u.theme == "light"


@pytest.mark.django_db
class TestThemeUpdateView:
    """ThemeUpdateView accepts every valid theme, including fantasy."""

    def test_requires_login(self, client):
        resp = client.post(reverse("profile:theme-update"), {"theme": "fantasy"})
        assert resp.status_code == 302
        assert "login" in resp.url

    @pytest.mark.parametrize("theme", ["light", "dark", "pastel", "lemonade", "fantasy"])
    def test_accepts_valid_themes(self, authenticated_client, user, theme):
        resp = authenticated_client.post(reverse("profile:theme-update"), {"theme": theme})
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.theme == theme

    def test_rejects_invalid_theme(self, authenticated_client, user):
        resp = authenticated_client.post(reverse("profile:theme-update"), {"theme": "neon"})
        assert resp.status_code == 400
        user.refresh_from_db()
        assert user.theme != "neon"

    def test_missing_theme_rejected(self, authenticated_client):
        resp = authenticated_client.post(reverse("profile:theme-update"), {})
        assert resp.status_code == 400


@pytest.mark.django_db
class TestBaseTemplateThemeRendering:
    """The <html data-theme> attribute should reflect the new default."""

    def test_anonymous_visitor_gets_fantasy(self, client):
        html = client.get(reverse("home")).content.decode()
        assert 'data-theme="fantasy"' in html

    def test_authenticated_default_user_gets_fantasy(self, authenticated_client):
        html = authenticated_client.get(reverse("home")).content.decode()
        assert 'data-theme="fantasy"' in html

    def test_authenticated_light_user_keeps_light(self, client):
        User.objects.create_user(username="li", email="li@e.com", password="x", theme="light")
        client.login(username="li", password="x")
        html = client.get(reverse("home")).content.decode()
        assert 'data-theme="light"' in html

    def test_authenticated_dark_user_keeps_dark(self, client):
        User.objects.create_user(username="dk", email="dk@e.com", password="x", theme="dark")
        client.login(username="dk", password="x")
        html = client.get(reverse("home")).content.decode()
        assert 'data-theme="dark"' in html
