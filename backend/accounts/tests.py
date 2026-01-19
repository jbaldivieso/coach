import pytest
from django.contrib.auth.models import User


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/api/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCSRFEndpoint:
    def test_get_csrf_token(self, client):
        response = client.get("/api/accounts/csrf/")
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 0


class TestLoginEndpoint:
    def test_login_success(self, client, user):
        response = client.post(
            "/api/accounts/login/",
            data={"username": "testuser", "password": "testpass123"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data

    def test_login_invalid_credentials(self, client, user):
        response = client.post(
            "/api/accounts/login/",
            data={"username": "testuser", "password": "wrongpassword"},
            content_type="application/json",
        )
        assert response.status_code == 401
        assert response.json() == {"message": "Invalid credentials"}

    @pytest.mark.django_db
    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/accounts/login/",
            data={"username": "nouser", "password": "testpass123"},
            content_type="application/json",
        )
        assert response.status_code == 401
        assert response.json() == {"message": "Invalid credentials"}


class TestLogoutEndpoint:
    def test_logout_success(self, authenticated_client):
        response = authenticated_client.post("/api/accounts/logout/")
        assert response.status_code == 200
        assert response.json() == {"message": "Logged out successfully"}

    def test_logout_unauthenticated(self, client):
        response = client.post("/api/accounts/logout/")
        assert response.status_code == 401


class TestMeEndpoint:
    def test_me_authenticated(self, authenticated_client, user):
        response = authenticated_client.get("/api/accounts/me/")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["id"] == user.id

    def test_me_unauthenticated(self, client):
        response = client.get("/api/accounts/me/")
        assert response.status_code == 401
