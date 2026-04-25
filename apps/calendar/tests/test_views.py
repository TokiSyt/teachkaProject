import pytest
from django.urls import reverse

from apps.calendar.models import Event


@pytest.fixture
def event(user):
    return Event.objects.create(
        user=user,
        title="Test event",
        subject="Math",
        start_datetime="2026-04-15 09:00:00+00:00",
        end_datetime="2026-04-15 10:00:00+00:00",
    )


@pytest.mark.django_db
class TestCalendarHomeView:
    def test_requires_login(self, client):
        url = reverse("calendar_app:home")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.url

    def test_authenticated_user_can_access(self, authenticated_client):
        url = reverse("calendar_app:home")
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_month_navigation_params(self, authenticated_client):
        url = reverse("calendar_app:home") + "?year=2026&month=4"
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.context["year"] == 2026
        assert response.context["month"] == 4


@pytest.mark.django_db
class TestEventCreateView:
    def test_requires_login(self, client):
        url = reverse("calendar_app:event_create")
        response = client.get(url)
        assert response.status_code == 302

    def test_get_form(self, authenticated_client):
        url = reverse("calendar_app:event_create")
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_event(self, authenticated_client):
        url = reverse("calendar_app:event_create")
        data = {
            "title": "New lesson",
            "subject": "History",
            "start_datetime": "2026-04-20T09:00",
            "end_datetime": "2026-04-20T10:00",
            "all_day": False,
            "description": "",
            "notes": "",
            "recurrence": "none",
            "recurrence_end": "",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302
        assert Event.objects.filter(title="New lesson").exists()

    def test_user_isolation(self, authenticated_client, other_user):
        other_event = Event.objects.create(
            user=other_user,
            title="Other user event",
            start_datetime="2026-04-15 09:00:00+00:00",
            end_datetime="2026-04-15 10:00:00+00:00",
        )
        url = reverse("calendar_app:event_edit", args=[other_event.pk])
        response = authenticated_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestEventUpdateView:
    def test_requires_login(self, client, event):
        url = reverse("calendar_app:event_edit", args=[event.pk])
        response = client.get(url)
        assert response.status_code == 302

    def test_get_form(self, authenticated_client, event):
        url = reverse("calendar_app:event_edit", args=[event.pk])
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_event(self, authenticated_client, event):
        url = reverse("calendar_app:event_edit", args=[event.pk])
        data = {
            "title": "Updated title",
            "subject": "Science",
            "start_datetime": "2026-04-15T09:00",
            "end_datetime": "2026-04-15T10:00",
            "all_day": False,
            "description": "",
            "notes": "",
            "recurrence": "none",
            "recurrence_end": "",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302
        event.refresh_from_db()
        assert event.title == "Updated title"


@pytest.mark.django_db
class TestEventDeleteView:
    def test_requires_login(self, client, event):
        url = reverse("calendar_app:event_delete", args=[event.pk])
        response = client.get(url)
        assert response.status_code == 302

    def test_confirm_page(self, authenticated_client, event):
        url = reverse("calendar_app:event_delete", args=[event.pk])
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_delete_event(self, authenticated_client, event):
        pk = event.pk
        url = reverse("calendar_app:event_delete", args=[pk])
        response = authenticated_client.post(url)
        assert response.status_code == 302
        assert not Event.objects.filter(pk=pk).exists()
