import pytest
from django.contrib.auth.models import User


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        password="testpass123",
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return a client logged in as the test user."""
    client.login(username="testuser", password="testpass123")
    return client
