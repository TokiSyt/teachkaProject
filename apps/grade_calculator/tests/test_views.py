import pytest
from django.urls import reverse


class TestGradeCalculatorView:
    @pytest.fixture
    def url(self):
        return reverse("grade_calculator:grade_calculator")

    def test_requires_login(self, client, url):
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.url

    def test_get_renders_form(self, authenticated_client, url):
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "form" in response.context

    def test_post_valid_data_returns_grades(self, authenticated_client, url):
        response = authenticated_client.post(url, {"max_points": 100, "rounding_option": 1})
        assert response.status_code == 200
        assert "score_range" in response.context
        assert len(response.context["score_range"]) == 10

    def test_post_with_decimal_rounding(self, authenticated_client, url):
        response = authenticated_client.post(url, {"max_points": 100, "rounding_option": 2})
        assert response.status_code == 200
        assert "score_range" in response.context

    def test_post_invalid_data_shows_errors(self, authenticated_client, url):
        response = authenticated_client.post(url, {"max_points": -10, "rounding_option": 1})
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_post_missing_data_shows_errors(self, authenticated_client, url):
        response = authenticated_client.post(url, {})
        assert response.status_code == 200
        assert response.context["form"].errors
