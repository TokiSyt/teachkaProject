"""
Root pytest configuration for Teachka.

Contains fixtures shared across all apps.
"""

import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user(db):
    """Create a test user."""
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return a Django test client logged in as the test user."""
    client.login(username="testuser", password="testpass123")
    return client


@pytest.fixture
def other_user(db):
    """Create another test user for permission testing."""
    User = get_user_model()
    return User.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="otherpass123",
    )
