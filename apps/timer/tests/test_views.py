import json

import pytest
from django.urls import reverse

from apps.users.models import UserStats


@pytest.mark.django_db
class TestHomeView:
    """Tests for Timer HomeView."""

    @pytest.fixture
    def url(self):
        return reverse("timer:home")

    def test_requires_login(self, client, url):
        """Unauthenticated users are redirected to login."""
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.url

    def test_get_returns_200(self, authenticated_client, url):
        """Authenticated users can access the page."""
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_uses_correct_template(self, authenticated_client, url):
        """View uses the timer home template."""
        response = authenticated_client.get(url)
        assert "timer/home.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestStopwatchViewGet:
    """Tests for StopwatchView GET requests."""

    @pytest.fixture
    def url(self):
        return reverse("timer:stopwatch")

    def test_requires_login(self, client, url):
        """Unauthenticated users are redirected to login."""
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.url

    def test_get_returns_200(self, authenticated_client, url):
        """Authenticated users can access the page."""
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_uses_correct_template(self, authenticated_client, url):
        """View uses the stopwatch template."""
        response = authenticated_client.get(url)
        assert "timer/stopwatch.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestStopwatchViewPost:
    """Tests for StopwatchView POST tracking."""

    @pytest.fixture
    def url(self):
        return reverse("timer:stopwatch")

    def test_start_increments_stopwatch_starts(self, authenticated_client, url, user):
        """POST with action=start increments stopwatch_starts."""
        response = authenticated_client.post(url, {"action": "start"})
        assert response.status_code == 200
        assert json.loads(response.content) == {"status": "ok"}
        stats = UserStats.objects.get(user=user)
        assert stats.stopwatch_starts == 1

    def test_start_increments_multiple_times(self, authenticated_client, url, user):
        """Multiple start actions increment correctly."""
        authenticated_client.post(url, {"action": "start"})
        authenticated_client.post(url, {"action": "start"})
        authenticated_client.post(url, {"action": "start"})
        stats = UserStats.objects.get(user=user)
        assert stats.stopwatch_starts == 3

    def test_flag_increments_stopwatch_flags(self, authenticated_client, url, user):
        """POST with action=flag increments stopwatch_flags."""
        response = authenticated_client.post(url, {"action": "flag"})
        assert response.status_code == 200
        stats = UserStats.objects.get(user=user)
        assert stats.stopwatch_flags == 1

    def test_stop_adds_elapsed_time(self, authenticated_client, url, user):
        """POST with action=stop adds elapsed ms to total."""
        response = authenticated_client.post(url, {"action": "stop", "elapsed": "5000"})
        assert response.status_code == 200
        stats = UserStats.objects.get(user=user)
        assert stats.stopwatch_total_ms == 5000

    def test_stop_accumulates_elapsed_time(self, authenticated_client, url, user):
        """Multiple stops accumulate total ms."""
        authenticated_client.post(url, {"action": "stop", "elapsed": "3000"})
        authenticated_client.post(url, {"action": "stop", "elapsed": "7000"})
        stats = UserStats.objects.get(user=user)
        assert stats.stopwatch_total_ms == 10000

    def test_stop_with_zero_elapsed_does_not_save(self, authenticated_client, url, user):
        """POST with elapsed=0 does not update total."""
        response = authenticated_client.post(url, {"action": "stop", "elapsed": "0"})
        assert response.status_code == 200
        stats = UserStats.objects.get(user=user)
        assert stats.stopwatch_total_ms == 0

    def test_invalid_action_returns_400(self, authenticated_client, url):
        """POST with unknown action returns 400."""
        response = authenticated_client.post(url, {"action": "invalid"})
        assert response.status_code == 400
        assert json.loads(response.content) == {"status": "error"}

    def test_missing_action_returns_400(self, authenticated_client, url):
        """POST without action returns 400."""
        response = authenticated_client.post(url, {})
        assert response.status_code == 400

    def test_post_requires_login(self, client, url):
        """Unauthenticated POST is redirected."""
        response = client.post(url, {"action": "start"})
        assert response.status_code == 302

    def test_creates_stats_if_missing(self, authenticated_client, url, user):
        """UserStats is auto-created on first POST."""
        assert not UserStats.objects.filter(user=user).exists()
        authenticated_client.post(url, {"action": "start"})
        assert UserStats.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestCountdownViewGet:
    """Tests for TimerView (countdown) GET requests."""

    @pytest.fixture
    def url(self):
        return reverse("timer:countdown")

    def test_requires_login(self, client, url):
        """Unauthenticated users are redirected to login."""
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.url

    def test_get_returns_200(self, authenticated_client, url):
        """Authenticated users can access the page."""
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_uses_correct_template(self, authenticated_client, url):
        """View uses the countdown template."""
        response = authenticated_client.get(url)
        assert "timer/countdown.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestCountdownViewPost:
    """Tests for TimerView (countdown) POST tracking."""

    @pytest.fixture
    def url(self):
        return reverse("timer:countdown")

    def test_start_increments_countdown_starts(self, authenticated_client, url, user):
        """POST with action=start increments countdown_starts."""
        response = authenticated_client.post(url, {"action": "start"})
        assert response.status_code == 200
        assert json.loads(response.content) == {"status": "ok"}
        stats = UserStats.objects.get(user=user)
        assert stats.countdown_starts == 1

    def test_stop_adds_elapsed_time(self, authenticated_client, url, user):
        """POST with action=stop adds elapsed ms to total."""
        response = authenticated_client.post(url, {"action": "stop", "elapsed": "60000"})
        assert response.status_code == 200
        stats = UserStats.objects.get(user=user)
        assert stats.countdown_total_ms == 60000

    def test_stop_accumulates_elapsed_time(self, authenticated_client, url, user):
        """Multiple stops accumulate total ms."""
        authenticated_client.post(url, {"action": "stop", "elapsed": "10000"})
        authenticated_client.post(url, {"action": "stop", "elapsed": "20000"})
        stats = UserStats.objects.get(user=user)
        assert stats.countdown_total_ms == 30000

    def test_stop_with_zero_elapsed_does_not_save(self, authenticated_client, url, user):
        """POST with elapsed=0 does not update total."""
        authenticated_client.post(url, {"action": "stop", "elapsed": "0"})
        stats = UserStats.objects.get(user=user)
        assert stats.countdown_total_ms == 0

    def test_invalid_action_returns_400(self, authenticated_client, url):
        """POST with unknown action returns 400."""
        response = authenticated_client.post(url, {"action": "invalid"})
        assert response.status_code == 400

    def test_missing_action_returns_400(self, authenticated_client, url):
        """POST without action returns 400."""
        response = authenticated_client.post(url, {})
        assert response.status_code == 400

    def test_post_requires_login(self, client, url):
        """Unauthenticated POST is redirected."""
        response = client.post(url, {"action": "start"})
        assert response.status_code == 302

    def test_creates_stats_if_missing(self, authenticated_client, url, user):
        """UserStats is auto-created on first POST."""
        assert not UserStats.objects.filter(user=user).exists()
        authenticated_client.post(url, {"action": "start"})
        assert UserStats.objects.filter(user=user).exists()
