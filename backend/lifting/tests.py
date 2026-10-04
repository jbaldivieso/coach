import datetime as dt

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
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Session"
        assert data["status"] == "done"
        assert data["exercises"] == []

    def test_create_session_unauthenticated(self, client):
        response = client.post(
            "/api/lifting/sessions/",
            data={"title": "New", "date": "2024-01-20"},
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
        assert data["sets"] == [{"weight": 225, "reps": 5, "done": True}] * 3

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
        assert response.json()["sets"] == [{"weight": 145, "reps": 10, "done": True}]

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


# ============ Exercise Title Autocomplete Tests ============


def _titles(response):
    return [item["title"] for item in response.json()["suggestions"]]


class TestExerciseTitleAutocomplete:
    def test_requires_auth(self, client):
        response = client.get("/api/lifting/exercises/autocomplete/?q=bench")
        assert response.status_code == 401

    def test_empty_query_returns_recent(self, authenticated_client, exercise):
        response = authenticated_client.get("/api/lifting/exercises/autocomplete/?q=")
        assert response.status_code == 200
        assert _titles(response) == ["Bench Press"]

    def test_matches_substring(self, authenticated_client, exercise):
        # exercise fixture has title "Bench Press"
        response = authenticated_client.get("/api/lifting/exercises/autocomplete/?q=ench")
        assert response.status_code == 200
        assert "Bench Press" in _titles(response)

    def test_case_insensitive(self, authenticated_client, exercise):
        response = authenticated_client.get("/api/lifting/exercises/autocomplete/?q=bench")
        assert response.status_code == 200
        assert "Bench Press" in _titles(response)

    def test_distinct_titles_with_count_and_last_date(self, authenticated_client, user):
        s1 = Session.objects.create(title="Session A", date="2024-01-01", user=user)
        s2 = Session.objects.create(title="Session B", date="2024-01-02", user=user)
        Exercise.objects.create(title="Squat", session=s1, sets=[], rest_seconds=90)
        Exercise.objects.create(title="Squat", session=s2, sets=[], rest_seconds=90)

        response = authenticated_client.get("/api/lifting/exercises/autocomplete/?q=squat")
        assert response.status_code == 200
        assert response.json()["suggestions"] == [
            {"title": "Squat", "count": 2, "last_date": "2024-01-02"}
        ]

    def test_ordered_by_recency(self, authenticated_client, user):
        old = Session.objects.create(title="Old", date="2024-01-01", user=user)
        new = Session.objects.create(title="New", date="2024-02-01", user=user)
        Exercise.objects.create(title="Tricep Pushdown", session=old, sets=[], rest_seconds=60)
        Exercise.objects.create(title="Tricep Dips", session=new, sets=[], rest_seconds=60)

        response = authenticated_client.get("/api/lifting/exercises/autocomplete/?q=tricep")
        assert _titles(response) == ["Tricep Dips", "Tricep Pushdown"]

    def test_ignores_planned_sessions(self, authenticated_client, user):
        planned = Session.objects.create(title="P", date="2024-01-01", status="planned", user=user)
        Exercise.objects.create(title="Zercher Squat", session=planned, sets=[], rest_seconds=60)
        response = authenticated_client.get("/api/lifting/exercises/autocomplete/?q=zercher")
        assert _titles(response) == []

    def test_only_returns_own_exercises(self, authenticated_client, other_session):
        Exercise.objects.create(
            title="Deadlift", session=other_session, sets=[], rest_seconds=120
        )
        response = authenticated_client.get("/api/lifting/exercises/autocomplete/?q=dead")
        assert response.status_code == 200
        assert response.json()["suggestions"] == []

    def test_returns_at_most_8_results(self, authenticated_client, session):
        for i in range(10):
            Exercise.objects.create(
                title=f"Exercise {i:02d}", session=session, sets=[], rest_seconds=60
            )
        response = authenticated_client.get("/api/lifting/exercises/autocomplete/?q=exercise")
        assert response.status_code == 200
        assert len(response.json()["suggestions"]) == 8


# ============ Redesign: statuses, supersets, history ============


def _ex(session, title, sets, position=0, rest=90, comments="", group=None):
    return Exercise.objects.create(
        title=title,
        session=session,
        sets=sets,
        rest_seconds=rest,
        comments=comments,
        position=position,
        superset_group=group,
    )


@pytest.fixture
def active_session(db, user):
    session = Session.objects.create(
        title="Upper B", date="2024-03-01", status="active", user=user
    )
    _ex(session, "Bench Press", [
        {"weight": 155, "reps": 5, "done": True},
        {"weight": 155, "reps": 5, "done": True},
        {"weight": 155, "reps": 5, "done": False},
    ], position=0)
    _ex(session, "Row", [{"weight": 100, "reps": 8, "done": True}], position=1, group=1)
    _ex(session, "Face Pull", [{"weight": 30, "reps": 15, "done": False}], position=2, group=1)
    _ex(session, "Curl", [{"weight": 25, "reps": 10, "done": False}], position=3)
    return session


class TestCreateSessionWithExercises:
    URL = "/api/lifting/sessions/with-exercises/"

    def _payload(self, **overrides):
        payload = {
            "title": "Lower A",
            "date": "2024-01-20",
            "exercises": [
                {"title": "Squat", "rest_seconds": 180, "sets": [{"weight": 225, "reps": 5, "done": False}]},
                {"title": "RDL", "rest_seconds": 90, "superset_group": 1, "sets": [{"weight": 135, "reps": 8, "done": False}]},
                {"title": "Plank", "rest_seconds": 90, "superset_group": 1, "sets": [{"weight": None, "reps": 60, "done": False}]},
            ],
        }
        payload.update(overrides)
        return payload

    def test_defaults_to_done(self, authenticated_client):
        response = authenticated_client.post(self.URL, data=self._payload(), content_type="application/json")
        assert response.status_code == 201
        assert response.json()["status"] == "done"

    def test_planned_allows_future_date(self, authenticated_client):
        future = str(dt.date.today() + dt.timedelta(days=3))
        response = authenticated_client.post(
            self.URL, data=self._payload(status="planned", date=future), content_type="application/json"
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "planned"
        assert data["started_at"] is None

    def test_active_rejects_future_date(self, authenticated_client):
        future = str(dt.date.today() + dt.timedelta(days=3))
        response = authenticated_client.post(
            self.URL, data=self._payload(status="active", date=future), content_type="application/json"
        )
        assert response.status_code == 400

    def test_active_sets_started_at(self, authenticated_client):
        response = authenticated_client.post(
            self.URL, data=self._payload(status="active"), content_type="application/json"
        )
        assert response.status_code == 201
        assert response.json()["started_at"] is not None

    def test_invalid_status(self, authenticated_client):
        response = authenticated_client.post(
            self.URL, data=self._payload(status="someday"), content_type="application/json"
        )
        assert response.status_code == 400

    def test_supersets_and_positions(self, authenticated_client):
        response = authenticated_client.post(self.URL, data=self._payload(), content_type="application/json")
        exercises = response.json()["exercises"]
        assert [e["position"] for e in exercises] == [0, 1, 2]
        assert [e["superset_group"] for e in exercises] == [None, 1, 1]
        assert exercises[2]["sets"][0]["weight"] is None

    def test_float_weights(self, authenticated_client):
        payload = self._payload()
        payload["exercises"][0]["sets"] = [{"weight": 152.5, "reps": 5}]
        response = authenticated_client.post(self.URL, data=payload, content_type="application/json")
        assert response.json()["exercises"][0]["sets"] == [{"weight": 152.5, "reps": 5, "done": True}]


class TestUpdateSessionWithExercises:
    def test_upserts_and_deletes(self, authenticated_client, session, exercise):
        doomed = _ex(session, "Doomed", [], position=1)
        response = authenticated_client.put(
            f"/api/lifting/sessions/{session.id}/with-exercises/",
            data={
                "title": "Renamed",
                "date": "2024-01-15",
                "exercises": [
                    {"title": "New One", "rest_seconds": 60, "sets": [{"weight": 10, "reps": 10}]},
                    {"id": exercise.id, "title": "Bench Press", "rest_seconds": 120, "sets": [{"weight": 140, "reps": 5}]},
                ],
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Renamed"
        assert [e["title"] for e in data["exercises"]] == ["New One", "Bench Press"]
        assert data["exercises"][1]["id"] == exercise.id
        assert data["exercises"][1]["rest_seconds"] == 120
        assert not Exercise.objects.filter(id=doomed.id).exists()

    def test_cannot_touch_other_users_exercise(self, authenticated_client, session, other_session):
        theirs = _ex(other_session, "Theirs", [{"weight": 1, "reps": 1}])
        response = authenticated_client.put(
            f"/api/lifting/sessions/{session.id}/with-exercises/",
            data={
                "title": "T",
                "date": "2024-01-15",
                "exercises": [{"id": theirs.id, "title": "Mine now", "rest_seconds": 60, "sets": []}],
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        theirs.refresh_from_db()
        assert theirs.title == "Theirs"

    def test_other_user_session(self, authenticated_client, other_session):
        response = authenticated_client.put(
            f"/api/lifting/sessions/{other_session.id}/with-exercises/",
            data={"title": "T", "date": "2024-01-15", "exercises": []},
            content_type="application/json",
        )
        assert response.status_code == 404


class TestCreateExerciseInsert:
    def test_insert_at_position_shifts_later(self, authenticated_client, active_session):
        response = authenticated_client.post(
            f"/api/lifting/sessions/{active_session.id}/exercises/",
            data={"title": "Dip", "rest_seconds": 60, "position": 1, "sets": [{"weight": None, "reps": 10, "done": False}]},
            content_type="application/json",
        )
        assert response.status_code == 201
        titles = list(active_session.exercises.values_list("title", flat=True))
        assert titles == ["Bench Press", "Dip", "Row", "Face Pull", "Curl"]

    def test_append_after_single_exercise(self, authenticated_client, session, exercise):
        response = authenticated_client.post(
            f"/api/lifting/sessions/{session.id}/exercises/",
            data={"title": "Dip", "rest_seconds": 60, "sets": []},
            content_type="application/json",
        )
        assert response.json()["position"] == 1


class TestStartSession:
    def test_start_planned(self, authenticated_client, user):
        planned = Session.objects.create(title="P", date="2030-01-01", status="planned", user=user)
        response = authenticated_client.post(
            f"/api/lifting/sessions/{planned.id}/start/",
            data={"date": "2024-05-05"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["started_at"] is not None
        assert data["date"] == "2024-05-05"

    def test_start_without_body_dates_today(self, authenticated_client, user):
        planned = Session.objects.create(title="P", date="2030-01-01", status="planned", user=user)
        response = authenticated_client.post(f"/api/lifting/sessions/{planned.id}/start/", data={}, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["date"] == str(dt.date.today())

    def test_cannot_start_done(self, authenticated_client, session):
        response = authenticated_client.post(f"/api/lifting/sessions/{session.id}/start/", data={}, content_type="application/json")
        assert response.status_code == 400

    def test_other_user(self, authenticated_client, other_session):
        other_session.status = "planned"
        other_session.save()
        response = authenticated_client.post(f"/api/lifting/sessions/{other_session.id}/start/", data={}, content_type="application/json")
        assert response.status_code == 404


class TestFinishSession:
    def test_drops_undone_sets_and_empty_exercises(self, authenticated_client, active_session):
        response = authenticated_client.post(
            f"/api/lifting/sessions/{active_session.id}/finish/",
            data={"comments": "Gym was hot"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["finished_at"] is not None
        assert data["comments"] == "Gym was hot"
        exercises = data["exercises"]
        assert [e["title"] for e in exercises] == ["Bench Press", "Row"]
        assert len(exercises[0]["sets"]) == 2
        assert all(s["done"] for e in exercises for s in e["sets"])
        assert [e["position"] for e in exercises] == [0, 1]
        # Face Pull was dropped, so Row's superset dissolves
        assert exercises[1]["superset_group"] is None

    def test_without_comments_keeps_existing(self, authenticated_client, active_session):
        active_session.comments = "Keep me"
        active_session.save()
        response = authenticated_client.post(f"/api/lifting/sessions/{active_session.id}/finish/", data={}, content_type="application/json")
        assert response.json()["comments"] == "Keep me"

    def test_cannot_finish_planned(self, authenticated_client, user):
        planned = Session.objects.create(title="P", date="2024-01-01", status="planned", user=user)
        response = authenticated_client.post(f"/api/lifting/sessions/{planned.id}/finish/", data={}, content_type="application/json")
        assert response.status_code == 400

    def test_other_user(self, authenticated_client, other_session):
        other_session.status = "active"
        other_session.save()
        response = authenticated_client.post(f"/api/lifting/sessions/{other_session.id}/finish/", data={}, content_type="application/json")
        assert response.status_code == 404


class TestOpenSessions:
    def test_lists_active_then_planned(self, authenticated_client, user, session, active_session):
        planned = Session.objects.create(title="Later", date="2030-01-01", status="planned", user=user)
        response = authenticated_client.get("/api/lifting/sessions/open/")
        assert response.status_code == 200
        assert [s["id"] for s in response.json()] == [active_session.id, planned.id]

    def test_only_own(self, authenticated_client, other_session):
        other_session.status = "planned"
        other_session.save()
        response = authenticated_client.get("/api/lifting/sessions/open/")
        assert response.json() == []


class TestListSessionsFilters:
    def test_defaults_to_done(self, authenticated_client, session, active_session):
        response = authenticated_client.get("/api/lifting/sessions/")
        assert [s["id"] for s in response.json()["items"]] == [session.id]

    def test_status_filter(self, authenticated_client, session, active_session):
        response = authenticated_client.get("/api/lifting/sessions/?status=active")
        assert [s["id"] for s in response.json()["items"]] == [active_session.id]

    def test_month_filter(self, authenticated_client, user, session):
        feb = Session.objects.create(title="Feb", date="2024-02-10", user=user)
        response = authenticated_client.get("/api/lifting/sessions/?month=2024-02")
        assert [s["id"] for s in response.json()["items"]] == [feb.id]

    def test_bad_month(self, authenticated_client):
        response = authenticated_client.get("/api/lifting/sessions/?month=feb")
        assert response.status_code == 400


class TestCalendar:
    def test_month_excludes_planned(self, authenticated_client, user, session):
        Session.objects.create(title="P", date="2024-01-20", status="planned", user=user)
        response = authenticated_client.get("/api/lifting/sessions/calendar/?year=2024&month=1")
        assert [s["date"] for s in response.json()["sessions"]] == ["2024-01-15"]

    def test_year_returns_12_months_ending_at_end(self, authenticated_client, session, other_session):
        response = authenticated_client.get("/api/lifting/sessions/calendar/year/?end=2024-06")
        assert response.status_code == 200
        months = response.json()["months"]
        assert len(months) == 12
        assert (months[0]["year"], months[0]["month"]) == (2023, 7)
        assert (months[-1]["year"], months[-1]["month"]) == (2024, 6)
        jan = next(m for m in months if m["month"] == 1)
        assert jan["sessions"] == [{"date": "2024-01-15", "session_id": session.id}]
        assert sum(len(m["sessions"]) for m in months) == 1

    def test_year_bad_end(self, authenticated_client):
        response = authenticated_client.get("/api/lifting/sessions/calendar/year/?end=2024")
        assert response.status_code == 400


class TestExerciseHistory:
    URL = "/api/lifting/exercises/history/"

    @pytest.fixture
    def outings(self, user):
        sessions = []
        for i, day in enumerate(["2024-01-01", "2024-01-08", "2024-01-15", "2024-01-22"]):
            s = Session.objects.create(title=f"Upper {i}", date=day, user=user)
            _ex(s, "Bench Press", [{"weight": 135 + i * 5, "reps": 5, "done": True}], comments=f"note {i}")
            _ex(s, "Bench Press Incline", [{"weight": 95, "reps": 8, "done": True}], position=1)
            sessions.append(s)
        return sessions

    def test_exact_match_newest_first(self, authenticated_client, outings):
        response = authenticated_client.get(self.URL, {"title": "Bench Press"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert data["has_more"] is True
        assert [o["date"] for o in data["items"]] == ["2024-01-22", "2024-01-15", "2024-01-08"]
        assert data["items"][0]["comments"] == "note 3"
        assert data["items"][0]["session_title"] == "Upper 3"

    def test_pagination(self, authenticated_client, outings):
        response = authenticated_client.get(self.URL, {"title": "Bench Press", "limit": 3, "offset": 3})
        data = response.json()
        assert [o["date"] for o in data["items"]] == ["2024-01-01"]
        assert data["has_more"] is False

    def test_exclude_session(self, authenticated_client, outings):
        response = authenticated_client.get(
            self.URL, {"title": "Bench Press", "exclude_session": outings[-1].id}
        )
        assert response.json()["items"][0]["date"] == "2024-01-15"

    def test_done_sessions_and_sets_only(self, authenticated_client, user, outings):
        planned = Session.objects.create(title="P", date="2024-02-01", status="planned", user=user)
        _ex(planned, "Bench Press", [{"weight": 200, "reps": 5, "done": False}])
        mixed = Session.objects.create(title="M", date="2024-01-29", user=user)
        _ex(mixed, "Bench Press", [
            {"weight": 160, "reps": 5, "done": True},
            {"weight": 160, "reps": 5, "done": False},
        ])
        response = authenticated_client.get(self.URL, {"title": "Bench Press"})
        first = response.json()["items"][0]
        assert first["date"] == "2024-01-29"
        assert first["sets"] == [{"weight": 160, "reps": 5, "done": True}]

    def test_only_own(self, authenticated_client, other_session):
        _ex(other_session, "Bench Press", [{"weight": 1, "reps": 1, "done": True}])
        response = authenticated_client.get(self.URL, {"title": "Bench Press"})
        assert response.json()["total"] == 0

    def test_requires_auth(self, client):
        response = client.get(self.URL, {"title": "Bench Press"})
        assert response.status_code == 401


class TestSessionTitleAutocomplete:
    def test_counts_and_recency(self, authenticated_client, user):
        Session.objects.create(title="Lower A", date="2024-01-01", user=user)
        Session.objects.create(title="Lower A", date="2024-01-10", user=user)
        Session.objects.create(title="Lower B", date="2024-01-20", user=user)
        response = authenticated_client.get("/api/lifting/sessions/autocomplete/?q=lower")
        assert response.json()["suggestions"] == [
            {"title": "Lower B", "count": 1, "last_date": "2024-01-20"},
            {"title": "Lower A", "count": 2, "last_date": "2024-01-10"},
        ]

    def test_empty_query(self, authenticated_client, session):
        response = authenticated_client.get("/api/lifting/sessions/autocomplete/?q=")
        assert response.json()["suggestions"] == []


class TestSearch:
    def test_sessions_exercises_and_last_session(self, authenticated_client, search_sessions):
        response = authenticated_client.get("/api/lifting/search/?q=a")
        assert response.status_code == 200

        response = authenticated_client.get("/api/lifting/search/?q=lower")
        data = response.json()
        lower = search_sessions[1]
        assert data["sessions"] == [{"id": lower.id, "title": "Lower A", "date": "2024-01-17"}]
        assert data["last_session"] == data["sessions"][0]
        assert data["exercises"] == []

    def test_exercise_counts(self, authenticated_client, search_sessions):
        data = authenticated_client.get("/api/lifting/search/?q=bench").json()
        assert data["exercises"] == [{"title": "Bench Press", "count": 2, "last_date": "2024-01-17"}]
        assert data["last_session"] is None

    def test_empty_query(self, authenticated_client, search_sessions):
        data = authenticated_client.get("/api/lifting/search/?q=").json()
        assert data == {"sessions": [], "exercises": [], "last_session": None}

    def test_only_own(self, authenticated_client, other_session):
        data = authenticated_client.get("/api/lifting/search/?q=other").json()
        assert data["sessions"] == []

    def test_requires_auth(self, client):
        assert client.get("/api/lifting/search/?q=x").status_code == 401
