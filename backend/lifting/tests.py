import pytest
from django.contrib.auth.models import User
from .models import Session, Exercise


# ============ Fixtures ============

@pytest.fixture
def session(db, user):
    """Create a test session."""
    return Session.objects.create(
        title="Test Session",
        date="2024-01-15",
        comments="Test comments",
        session_type="volume",
        user=user,
    )


@pytest.fixture
def exercise(db, session):
    """Create a test exercise."""
    return Exercise.objects.create(
        title="Bench Press",
        session=session,
        weight_lbs=135,
        rest_seconds=90,
        reps=[10, 10, 8],
        comments="Felt good",
    )


@pytest.fixture
def other_user(db):
    """Create another user for authorization tests."""
    return User.objects.create_user(
        username="otheruser",
        password="otherpass123",
    )


@pytest.fixture
def other_session(db, other_user):
    """Create a session owned by another user."""
    return Session.objects.create(
        title="Other User Session",
        date="2024-01-15",
        session_type="weight",
        user=other_user,
    )


# ============ Session Endpoint Tests ============

class TestListSessions:
    def test_list_sessions_authenticated(self, authenticated_client, session):
        response = authenticated_client.get("/api/lifting/sessions/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Test Session"
        assert data["has_more"] is False

    def test_list_sessions_unauthenticated(self, client):
        response = client.get("/api/lifting/sessions/")
        assert response.status_code == 401

    def test_list_sessions_only_own(self, authenticated_client, session, other_session):
        response = authenticated_client.get("/api/lifting/sessions/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Test Session"


class TestCreateSession:
    def test_create_session(self, authenticated_client):
        response = authenticated_client.post(
            "/api/lifting/sessions/",
            data={
                "title": "New Session",
                "date": "2024-01-20",
                "comments": "New comments",
                "session_type": "weight",
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Session"
        assert data["session_type"] == "weight"
        assert data["exercises"] == []

    def test_create_session_unauthenticated(self, client):
        response = client.post(
            "/api/lifting/sessions/",
            data={"title": "New", "date": "2024-01-20", "session_type": "volume"},
            content_type="application/json",
        )
        assert response.status_code == 401


class TestGetSession:
    def test_get_session(self, authenticated_client, session, exercise):
        response = authenticated_client.get(f"/api/lifting/sessions/{session.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Session"
        assert len(data["exercises"]) == 1
        assert data["exercises"][0]["title"] == "Bench Press"

    def test_get_session_not_found(self, authenticated_client):
        response = authenticated_client.get("/api/lifting/sessions/9999/")
        assert response.status_code == 404

    def test_get_session_other_user(self, authenticated_client, other_session):
        response = authenticated_client.get(f"/api/lifting/sessions/{other_session.id}/")
        assert response.status_code == 404


class TestUpdateSession:
    def test_update_session(self, authenticated_client, session):
        response = authenticated_client.put(
            f"/api/lifting/sessions/{session.id}/",
            data={"title": "Updated Title"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_update_session_includes_exercises(self, authenticated_client, session, exercise):
        response = authenticated_client.put(
            f"/api/lifting/sessions/{session.id}/",
            data={"title": "Updated Title"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "exercises" in data
        assert len(data["exercises"]) == 1
        assert data["exercises"][0]["title"] == "Bench Press"

    def test_update_session_other_user(self, authenticated_client, other_session):
        response = authenticated_client.put(
            f"/api/lifting/sessions/{other_session.id}/",
            data={"title": "Hacked"},
            content_type="application/json",
        )
        assert response.status_code == 404


class TestDeleteSession:
    def test_delete_session(self, authenticated_client, session):
        response = authenticated_client.delete(f"/api/lifting/sessions/{session.id}/")
        assert response.status_code == 200
        assert not Session.objects.filter(id=session.id).exists()

    def test_delete_session_cascades_exercises(self, authenticated_client, session, exercise):
        response = authenticated_client.delete(f"/api/lifting/sessions/{session.id}/")
        assert response.status_code == 200
        assert not Exercise.objects.filter(id=exercise.id).exists()

    def test_delete_session_other_user(self, authenticated_client, other_session):
        response = authenticated_client.delete(f"/api/lifting/sessions/{other_session.id}/")
        assert response.status_code == 404


# ============ Exercise Endpoint Tests ============

class TestCreateExercise:
    def test_create_exercise(self, authenticated_client, session):
        response = authenticated_client.post(
            f"/api/lifting/sessions/{session.id}/exercises/",
            data={
                "title": "Squat",
                "weight_lbs": 225,
                "rest_seconds": 120,
                "reps": [5, 5, 5],
                "comments": "",
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Squat"
        assert data["reps"] == [5, 5, 5]

    def test_create_exercise_other_user_session(self, authenticated_client, other_session):
        response = authenticated_client.post(
            f"/api/lifting/sessions/{other_session.id}/exercises/",
            data={"title": "Squat", "rest_seconds": 90, "reps": [5]},
            content_type="application/json",
        )
        assert response.status_code == 404


class TestUpdateExercise:
    def test_update_exercise(self, authenticated_client, exercise):
        response = authenticated_client.put(
            f"/api/lifting/exercises/{exercise.id}/",
            data={"weight_lbs": 145},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["weight_lbs"] == 145

    def test_update_exercise_other_user(self, authenticated_client, other_session):
        other_exercise = Exercise.objects.create(
            title="Other Ex",
            session=other_session,
            rest_seconds=60,
            reps=[10],
        )
        response = authenticated_client.put(
            f"/api/lifting/exercises/{other_exercise.id}/",
            data={"title": "Hacked"},
            content_type="application/json",
        )
        assert response.status_code == 404


class TestDeleteExercise:
    def test_delete_exercise(self, authenticated_client, exercise):
        response = authenticated_client.delete(f"/api/lifting/exercises/{exercise.id}/")
        assert response.status_code == 200
        assert not Exercise.objects.filter(id=exercise.id).exists()

    def test_delete_exercise_other_user(self, authenticated_client, other_session):
        other_exercise = Exercise.objects.create(
            title="Other Ex",
            session=other_session,
            rest_seconds=60,
            reps=[10],
        )
        response = authenticated_client.delete(f"/api/lifting/exercises/{other_exercise.id}/")
        assert response.status_code == 404
