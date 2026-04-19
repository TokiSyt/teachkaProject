import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestCalendarHomeView:
    def test_requires_login(self, client):
        url = reverse("todo:home")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.url

    def test_authenticated_user_can_access(self, authenticated_client):
        url = reverse("todo:home")
        response = authenticated_client.get(url)
        assert response.status_code == 200
