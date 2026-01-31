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
        sets=[
            {"weight": 135, "reps": 10},
            {"weight": 135, "reps": 10},
            {"weight": 135, "reps": 8},
        ],
        rest_seconds=90,
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
                "sets": [
                    {"weight": 225, "reps": 5},
                    {"weight": 225, "reps": 5},
                    {"weight": 225, "reps": 5},
                ],
                "rest_seconds": 120,
                "comments": "",
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Squat"
        assert data["sets"] == [
            {"weight": 225, "reps": 5},
            {"weight": 225, "reps": 5},
            {"weight": 225, "reps": 5},
        ]

    def test_create_exercise_other_user_session(self, authenticated_client, other_session):
        response = authenticated_client.post(
            f"/api/lifting/sessions/{other_session.id}/exercises/",
            data={
                "title": "Squat",
                "rest_seconds": 90,
                "sets": [{"weight": None, "reps": 5}],
            },
            content_type="application/json",
        )
        assert response.status_code == 404


class TestUpdateExercise:
    def test_update_exercise(self, authenticated_client, exercise):
        response = authenticated_client.put(
            f"/api/lifting/exercises/{exercise.id}/",
            data={"sets": [{"weight": 145, "reps": 10}]},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["sets"] == [{"weight": 145, "reps": 10}]

    def test_update_exercise_other_user(self, authenticated_client, other_session):
        other_exercise = Exercise.objects.create(
            title="Other Ex",
            session=other_session,
            rest_seconds=60,
            sets=[{"weight": None, "reps": 10}],
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
            sets=[{"weight": None, "reps": 10}],
        )
        response = authenticated_client.delete(f"/api/lifting/exercises/{other_exercise.id}/")
        assert response.status_code == 404


# ============ Search Endpoint Tests ============


@pytest.fixture
def search_sessions(db, user):
    """Create multiple sessions with exercises for search testing."""
    session1 = Session.objects.create(
        title="Upper A",
        date="2024-01-15",
        session_type="volume",
        user=user,
    )
    Exercise.objects.create(
        title="Bench Press",
        session=session1,
        sets=[
            {"weight": 135, "reps": 10},
            {"weight": 135, "reps": 10},
            {"weight": 135, "reps": 8},
        ],
        rest_seconds=90,
    )
    Exercise.objects.create(
        title="Overhead Press",
        session=session1,
        sets=[
            {"weight": 95, "reps": 8},
            {"weight": 95, "reps": 8},
            {"weight": 95, "reps": 6},
        ],
        rest_seconds=90,
    )

    session2 = Session.objects.create(
        title="Lower A",
        date="2024-01-17",
        session_type="weight",
        user=user,
    )
    Exercise.objects.create(
        title="Squat",
        session=session2,
        sets=[
            {"weight": 225, "reps": 5},
            {"weight": 225, "reps": 5},
            {"weight": 225, "reps": 5},
        ],
        rest_seconds=120,
    )
    Exercise.objects.create(
        title="Bench Press",
        session=session2,
        sets=[
            {"weight": 145, "reps": 8},
            {"weight": 145, "reps": 8},
            {"weight": 145, "reps": 8},
        ],
        rest_seconds=90,
    )

    return [session1, session2]


class TestSearchAutocomplete:
    def test_autocomplete_requires_auth(self, client):
        response = client.get("/api/lifting/search/autocomplete/?q=ben")
        assert response.status_code == 401

    def test_autocomplete_requires_min_3_chars(self, authenticated_client, search_sessions):
        # 2 chars should return empty
        response = authenticated_client.get("/api/lifting/search/autocomplete/?q=be")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_autocomplete_returns_distinct_session_titles(self, authenticated_client, search_sessions):
        response = authenticated_client.get("/api/lifting/search/autocomplete/?q=Upper")
        assert response.status_code == 200
        data = response.json()

        session_items = [i for i in data["items"] if i["type"] == "session"]
        assert len(session_items) == 1
        assert session_items[0]["value"] == "Upper A"
        assert session_items[0]["label"] == "Upper A"
        assert session_items[0]["id"] is None  # No specific session ID

    def test_autocomplete_returns_distinct_exercises(self, authenticated_client, search_sessions):
        # "Bench Press" appears in both sessions, should only return once
        response = authenticated_client.get("/api/lifting/search/autocomplete/?q=Bench")
        assert response.status_code == 200
        data = response.json()

        exercise_items = [i for i in data["items"] if i["type"] == "exercise"]
        assert len(exercise_items) == 1
        assert exercise_items[0]["value"] == "Bench Press"

    def test_autocomplete_only_returns_own_data(self, authenticated_client, search_sessions, other_session):
        # Add an exercise to other_session
        Exercise.objects.create(
            title="Bench Press Special",
            session=other_session,
            rest_seconds=60,
            sets=[{"weight": None, "reps": 10}],
        )

        response = authenticated_client.get("/api/lifting/search/autocomplete/?q=Special")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


class TestSearchResults:
    def test_search_requires_auth(self, client):
        response = client.get("/api/lifting/search/results/")
        assert response.status_code == 401

    def test_search_no_filters_returns_all(self, authenticated_client, search_sessions):
        response = authenticated_client.get("/api/lifting/search/results/")
        assert response.status_code == 200
        data = response.json()
        # 2 exercises in session1, 2 in session2 = 4 total
        assert data["total"] == 4
        assert len(data["items"]) == 4

    def test_search_filter_by_session_title(self, authenticated_client, search_sessions):
        response = authenticated_client.get("/api/lifting/search/results/?session_title=Upper A")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["session_title"] == "Upper A" for item in data["items"])

    def test_search_filter_by_exercise_title(self, authenticated_client, search_sessions):
        response = authenticated_client.get("/api/lifting/search/results/?exercise_title=Bench Press")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["exercise_title"] == "Bench Press" for item in data["items"])

    def test_search_filter_combined(self, authenticated_client, search_sessions):
        response = authenticated_client.get(
            "/api/lifting/search/results/?session_title=Upper A&exercise_title=Bench Press"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        item = data["items"][0]
        assert item["session_title"] == "Upper A"
        assert item["exercise_title"] == "Bench Press"

    def test_search_only_returns_own_data(self, authenticated_client, search_sessions, other_session):
        # Add an exercise to other_session
        Exercise.objects.create(
            title="Other Exercise",
            session=other_session,
            rest_seconds=60,
            sets=[{"weight": None, "reps": 10}],
        )

        response = authenticated_client.get("/api/lifting/search/results/?exercise_title=Other Exercise")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_search_results_ordered_by_date_desc(self, authenticated_client, search_sessions):
        response = authenticated_client.get("/api/lifting/search/results/")
        assert response.status_code == 200
        data = response.json()
        # session2 is 2024-01-17, session1 is 2024-01-15
        # So session2's exercises should come first
        dates = [item["session_date"] for item in data["items"]]
        assert dates == sorted(dates, reverse=True)
