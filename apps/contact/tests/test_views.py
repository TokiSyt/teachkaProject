import pytest
from django.urls import reverse

from apps.contact.models import ContactMessage


@pytest.mark.django_db
class TestContactView:
    def test_get_renders_form(self, client):
        url = reverse("contact:contact")
        resp = client.get(url)
        assert resp.status_code == 200
        assert resp.context["selected_kind"] == "bug"

    def test_get_with_kind_query(self, client):
        url = reverse("contact:contact")
        resp = client.get(url, {"kind": "feature"})
        assert resp.context["selected_kind"] == "feature"

    def test_invalid_kind_falls_back_to_bug(self, client):
        resp = client.get(reverse("contact:contact"), {"kind": "garbage"})
        assert resp.context["selected_kind"] == "bug"

    def test_post_creates_message(self, client):
        url = reverse("contact:contact")
        resp = client.post(
            url,
            {
                "kind": "question",
                "subject": "How does the wheel work?",
                "body": "I cannot make the wheel spin from the dashboard.",
                "email": "user@example.com",
            },
        )
        assert resp.status_code == 302
        assert resp.url.endswith("?sent=1")
        msg = ContactMessage.objects.get()
        assert msg.kind == "question"
        assert msg.subject == "How does the wheel work?"
        assert msg.email == "user@example.com"
        assert msg.user is None

    def test_post_attaches_user_when_authenticated(self, authenticated_client, user):
        url = reverse("contact:contact")
        authenticated_client.post(
            url,
            {
                "kind": "bug",
                "subject": "Crash on save",
                "body": "Page returns 500 when I save the form.",
                "email": "",
            },
        )
        msg = ContactMessage.objects.get()
        assert msg.user == user

    def test_short_subject_invalid(self, client):
        url = reverse("contact:contact")
        resp = client.post(
            url,
            {"kind": "bug", "subject": "x", "body": "this is long enough text"},
        )
        assert resp.status_code == 200
        assert ContactMessage.objects.count() == 0
        assert b"too short" in resp.content.lower()

    def test_short_body_invalid(self, client):
        url = reverse("contact:contact")
        resp = client.post(
            url,
            {"kind": "bug", "subject": "Real subject", "body": "tiny"},
        )
        assert resp.status_code == 200
        assert ContactMessage.objects.count() == 0
