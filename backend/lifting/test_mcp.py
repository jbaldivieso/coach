import json
from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone
from oauth2_provider.models import AccessToken

from .models import Session, Template
from .tests import _ex, _template

URL = "/mcp"


def resource():
    return f"{settings.COACH_PUBLIC_URL}/mcp"


def make_token(user, token="token-1", scope="coach", resource_uris=None, expires_in=3600):
    return AccessToken.objects.create(
        user=user,
        token=token,
        scope=scope,
        resource=[resource()] if resource_uris is None else resource_uris,
        expires=timezone.now() + timedelta(seconds=expires_in),
    )


@pytest.fixture
def token(user):
    return make_token(user)


@pytest.fixture
def other_user(db):
    from django.contrib.auth.models import User

    return User.objects.create_user(username="otheruser", password="otherpass123")


def post(client, body, token="token-1"):
    """POST a JSON-RPC message. A str body is sent as-is."""
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
    return client.post(URL, data=body, content_type="application/json", **headers)


def rpc(client, method, params=None, id=1, token="token-1"):
    body = {"jsonrpc": "2.0", "id": id, "method": method}
    if params is not None:
        body["params"] = params
    response = post(client, body, token=token)
    assert response.status_code == 200, response.content
    assert response["Content-Type"] == "application/json"
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == id
    return data


def call(client, name, arguments=None):
    result = rpc(client, "tools/call", {"name": name, "arguments": arguments or {}})["result"]
    assert result["content"][0]["type"] == "text"
    if not result.get("isError"):
        assert json.loads(result["content"][0]["text"]) == result["structuredContent"]
    return result


def done_session(user, title="Upper A", date="2026-09-01", **kwargs):
    return Session.objects.create(title=title, date=date, status=Session.STATUS_DONE, user=user, **kwargs)


TEMPLATE = {
    "title": "Lower A",
    "comments": "Week 1",
    "exercises": [
        {"title": "Squat", "rest_seconds": 180, "sets": [{"weight": 225, "reps": 5}], "comments": "Belt"},
        {"title": "RDL", "rest_seconds": 90, "superset_group": 1, "sets": [{"weight": 135, "reps": 8}, {}]},
        {"title": "Plank", "rest_seconds": 90, "superset_group": 1, "sets": [{"reps": 60}, {"reps": 60}]},
    ],
}


@pytest.mark.django_db
class TestAuth:
    def _assert_401(self, response):
        assert response.status_code == 401
        assert response["WWW-Authenticate"] == (
            f'Bearer resource_metadata="{settings.COACH_PUBLIC_URL}/.well-known/oauth-protected-resource"'
        )

    def test_missing_token(self, client):
        self._assert_401(post(client, {"jsonrpc": "2.0", "id": 1, "method": "ping"}, token=None))

    def test_unknown_token(self, client, token):
        self._assert_401(post(client, {"jsonrpc": "2.0", "id": 1, "method": "ping"}, token="nope"))

    def test_expired_token(self, client, user):
        make_token(user, expires_in=-1)
        self._assert_401(post(client, {"jsonrpc": "2.0", "id": 1, "method": "ping"}))

    def test_wrong_scope(self, client, user):
        make_token(user, scope="read")
        response = post(client, {"jsonrpc": "2.0", "id": 1, "method": "ping"})
        assert response.status_code == 403
        assert response.json() == {"error": "insufficient_scope"}
        assert 'error="insufficient_scope"' in response["WWW-Authenticate"]

    def test_token_without_resource(self, client, user):
        make_token(user, resource_uris=[])
        self._assert_401(post(client, {"jsonrpc": "2.0", "id": 1, "method": "ping"}))

    def test_token_for_another_resource(self, client, user):
        make_token(user, resource_uris=["https://elsewhere.example/mcp"])
        self._assert_401(post(client, {"jsonrpc": "2.0", "id": 1, "method": "ping"}))

    def test_inactive_user(self, client, user):
        make_token(user)
        user.is_active = False
        user.save()
        self._assert_401(post(client, {"jsonrpc": "2.0", "id": 1, "method": "ping"}))

    def test_token_without_user(self, client, user):
        make_token(None)
        self._assert_401(post(client, {"jsonrpc": "2.0", "id": 1, "method": "ping"}))

    def test_valid_token(self, client, token):
        assert rpc(client, "ping")["result"] == {}

    def test_session_login_is_not_enough(self, authenticated_client):
        self._assert_401(post(authenticated_client, {"jsonrpc": "2.0", "id": 1, "method": "ping"}, token=None))


@pytest.mark.django_db
class TestTransport:
    @pytest.mark.parametrize("method", ["get", "delete"])
    def test_get_and_delete_not_allowed(self, client, token, method):
        response = getattr(client, method)(URL, HTTP_AUTHORIZATION="Bearer token-1")
        assert response.status_code == 405

    def test_no_trailing_slash_redirect(self, client, token):
        response = post(client, {"jsonrpc": "2.0", "id": 1, "method": "ping"})
        assert response.status_code == 200

    def test_no_csrf_needed(self, token):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        response = post(client, {"jsonrpc": "2.0", "id": 1, "method": "ping"})
        assert response.status_code == 200

    def test_notification_is_202(self, client, token):
        response = post(client, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        assert response.status_code == 202
        assert response.content == b""

    def test_response_is_202(self, client, token):
        response = post(client, {"jsonrpc": "2.0", "id": 9, "result": {}})
        assert response.status_code == 202
        assert response.content == b""

    def test_batch_rejected(self, client, token):
        response = post(client, [{"jsonrpc": "2.0", "id": 1, "method": "ping"}])
        assert response.status_code == 400
        assert response.json()["error"]["code"] == -32600

    def test_parse_error(self, client, token):
        response = post(client, "{not json")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == -32700

    def test_unknown_method(self, client, token):
        assert rpc(client, "resources/list")["error"]["code"] == -32601

    def test_unknown_tool(self, client, token):
        assert rpc(client, "tools/call", {"name": "delete_everything"})["error"]["code"] == -32602

    def test_tools_call_without_name(self, client, token):
        assert rpc(client, "tools/call", {})["error"]["code"] == -32602

    def test_tools_call_with_unhashable_name(self, client, token):
        assert rpc(client, "tools/call", {"name": ["list_templates"]})["error"]["code"] == -32602

    def test_unhashable_method(self, client, token):
        assert rpc(client, ["ping"])["error"]["code"] == -32600

    def test_unexpected_tool_failure_is_internal_error(self, client, token, monkeypatch):
        from . import mcp

        def boom(user, args):
            raise RuntimeError("boom")

        description, args, _ = mcp.TOOLS["list_templates"]
        monkeypatch.setitem(mcp.TOOLS, "list_templates", (description, args, boom))
        error = rpc(client, "tools/call", {"name": "list_templates"})["error"]
        assert error == {"code": -32603, "message": "Internal error"}


@pytest.mark.django_db
class TestInitialize:
    @pytest.mark.parametrize("version", ["2025-11-25", "2025-06-18", "2025-03-26"])
    def test_echoes_supported_version(self, client, token, version):
        result = rpc(client, "initialize", {"protocolVersion": version, "capabilities": {}, "clientInfo": {"name": "claude-ai"}})["result"]
        assert result["protocolVersion"] == version

    @pytest.mark.parametrize("version", ["2024-11-05", "2099-01-01", None])
    def test_unknown_version_gets_newest(self, client, token, version):
        result = rpc(client, "initialize", {"protocolVersion": version, "capabilities": {}})["result"]
        assert result["protocolVersion"] == "2025-11-25"

    def test_capabilities_and_instructions(self, client, token):
        result = rpc(client, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}})["result"]
        assert result["capabilities"] == {"tools": {}}
        assert result["serverInfo"]["name"] == "coach"
        instructions = result["instructions"]
        for phrase in ["lb", "bodyweight", "superset_group", "list_exercises", "6 sets"]:
            assert phrase in instructions


@pytest.mark.django_db
class TestToolsList:
    def _tools(self, client):
        return {t["name"]: t for t in rpc(client, "tools/list")["result"]["tools"]}

    def test_names(self, client, token):
        assert set(self._tools(client)) == {
            "list_exercises",
            "get_sessions",
            "get_exercise_history",
            "list_templates",
            "get_template",
            "create_template",
            "update_template",
            "archive_template",
            "restore_template",
        }

    def test_every_tool_has_description_and_object_schema(self, client, token):
        for tool in self._tools(client).values():
            assert tool["description"]
            assert tool["inputSchema"]["type"] == "object"

    def test_schemas_state_the_limits(self, client, token):
        tools = self._tools(client)
        create = tools["create_template"]["inputSchema"]
        assert set(create["required"]) == {"title", "exercises"}
        assert create["properties"]["title"]["maxLength"] == 100
        exercise = create["$defs"]["TemplateExerciseInputSchema"]
        assert exercise["properties"]["title"]["maxLength"] == 100
        assert exercise["properties"]["rest_seconds"]["minimum"] == 0
        assert exercise["properties"]["sets"]["maxItems"] == 6

        history = tools["get_exercise_history"]["inputSchema"]
        assert history["required"] == ["title"]
        assert history["properties"]["limit"]["maximum"] == 50
        assert history["properties"]["limit"]["default"] == 10

        update = tools["update_template"]["inputSchema"]
        assert set(update["required"]) == {"id", "title", "exercises"}

        sessions = tools["get_sessions"]["inputSchema"]
        assert set(sessions["required"]) == {"start", "end"}


@pytest.mark.django_db
class TestReadTools:
    def test_list_exercises(self, client, token, user):
        first = done_session(user, date="2026-08-01")
        _ex(first, "Squat", [{"weight": 225, "reps": 5, "done": True}])
        second = done_session(user, date="2026-09-01")
        _ex(second, "Squat", [{"weight": 230, "reps": 5, "done": True}])
        _ex(second, "Bench Press", [{"weight": 155, "reps": 5, "done": True}], position=1)
        exercises = call(client, "list_exercises")["structuredContent"]["exercises"]
        assert {e["title"]: e for e in exercises}["Squat"] == {
            "title": "Squat",
            "count": 2,
            "first_date": "2026-08-01",
            "last_date": "2026-09-01",
        }
        assert len(exercises) == 2

    def test_get_sessions(self, client, token, user):
        template = _template(user)
        session = done_session(user, date="2026-09-01", comments="Good day", template=template)
        _ex(session, "Squat", [{"weight": 225, "reps": 5, "done": True}], comments="Belt", rest=180)
        done_session(user, title="Too early", date="2026-07-01")
        result = call(client, "get_sessions", {"start": "2026-08-01", "end": "2026-09-30"})
        sessions = result["structuredContent"]["sessions"]
        assert [s["title"] for s in sessions] == ["Upper A"]
        s = sessions[0]
        assert s["date"] == "2026-09-01"
        assert s["comments"] == "Good day"
        assert s["template_id"] == template.id
        assert s["exercises"][0]["title"] == "Squat"
        assert s["exercises"][0]["rest_seconds"] == 180
        assert s["exercises"][0]["comments"] == "Belt"
        assert s["exercises"][0]["sets"] == [{"weight": 225, "reps": 5, "done": True}]

    def test_get_sessions_oldest_first_and_inclusive(self, client, token, user):
        done_session(user, title="B", date="2026-09-30")
        done_session(user, title="A", date="2026-09-01")
        sessions = call(client, "get_sessions", {"start": "2026-09-01", "end": "2026-09-30"})["structuredContent"]["sessions"]
        assert [s["title"] for s in sessions] == ["A", "B"]

    def test_get_sessions_capped_at_180_days(self, client, token):
        assert not call(client, "get_sessions", {"start": "2026-01-01", "end": "2026-06-30"}).get("isError")
        result = call(client, "get_sessions", {"start": "2026-01-01", "end": "2026-07-01"})
        assert result["isError"] is True
        assert "180" in result["content"][0]["text"]

    def test_get_sessions_end_before_start(self, client, token):
        assert call(client, "get_sessions", {"start": "2026-02-01", "end": "2026-01-01"})["isError"] is True

    def test_get_exercise_history(self, client, token, user):
        session = done_session(user)
        _ex(session, "Squat", [{"weight": 225, "reps": 5, "done": True}])
        history = call(client, "get_exercise_history", {"title": "Squat"})["structuredContent"]
        assert history["title"] == "Squat"
        assert history["total"] == 1
        assert history["items"][0]["sets"] == [{"weight": 225, "reps": 5, "done": True}]

    def test_list_templates(self, client, token, user):
        _template(user, title="Upper A")
        _template(user, title="Old", archived=True)
        assert [t["title"] for t in call(client, "list_templates")["structuredContent"]["templates"]] == ["Upper A"]
        everything = call(client, "list_templates", {"include_archived": True})["structuredContent"]["templates"]
        assert {t["title"] for t in everything} == {"Upper A", "Old"}

    def test_get_template(self, client, token, user):
        template = _template(user)
        result = call(client, "get_template", {"id": template.id})["structuredContent"]
        assert result["template"]["title"] == "Upper A"
        assert result["template"]["exercises"][0]["sets"] == [{"weight": 155, "reps": 5}]

    def test_get_missing_template(self, client, token):
        result = call(client, "get_template", {"id": 999})
        assert result["isError"] is True
        assert "999" in result["content"][0]["text"]


@pytest.mark.django_db
class TestWriteTools:
    def test_create_template(self, client, token, user):
        result = call(client, "create_template", TEMPLATE)
        assert not result.get("isError")
        template = Template.objects.get()
        assert template.user == user
        assert result["structuredContent"]["template"]["id"] == template.id
        assert [e.title for e in template.exercises.all()] == ["Squat", "RDL", "Plank"]
        assert template.exercises.all()[1].sets == [{"weight": 135, "reps": 8}, {"weight": None, "reps": None}]

    def test_create_warns_about_unknown_titles(self, client, token, user):
        _ex(done_session(user), "Squat", [{"weight": 225, "reps": 5, "done": True}])
        warnings = call(client, "create_template", {
            **TEMPLATE,
            "exercises": [{"title": "Squats", "rest_seconds": 90, "sets": [{}]}],
        })["structuredContent"]["warnings"]
        assert len(warnings) == 1
        assert '"Squat"' in warnings[0]

    def test_validation_error_is_tool_error(self, client, token):
        result = call(client, "create_template", {
            **TEMPLATE,
            "exercises": [{"title": "Squat", "rest_seconds": 90, "sets": [{"reps": 0}]}],
        })
        assert result["isError"] is True
        assert "reps" in result["content"][0]["text"]
        assert not Template.objects.exists()

    @pytest.mark.parametrize("weight", ["NaN", "Infinity", "-Infinity"])
    def test_non_finite_weight_is_tool_error(self, client, token, weight):
        exercise = '{"title": "Squat", "rest_seconds": 90, "sets": [{"weight": %s}]}' % weight
        arguments = '{"title": "Lower A", "exercises": [%s]}' % exercise
        body = '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "create_template", "arguments": %s}}' % arguments
        result = post(client, body).json()["result"]
        assert result["isError"] is True
        assert "weight" in result["content"][0]["text"]
        assert not Template.objects.exists()

    def test_bad_argument_types_are_tool_errors(self, client, token):
        result = call(client, "create_template", {"title": "No exercises key"})
        assert result["isError"] is True
        assert "exercises" in result["content"][0]["text"]

    def test_update_template(self, client, token, user):
        template = _template(user)
        result = call(client, "update_template", {
            "id": template.id,
            "title": "Upper B",
            "exercises": [{"title": "Row", "rest_seconds": 90, "sets": [{"weight": 100, "reps": 8}]}],
        })
        assert not result.get("isError")
        template.refresh_from_db()
        assert template.title == "Upper B"
        assert [e.title for e in template.exercises.all()] == ["Row"]
        assert result["structuredContent"]["template"]["title"] == "Upper B"
        assert "warnings" in result["structuredContent"]

    def test_archive_and_restore(self, client, token, user):
        template = _template(user)
        archived = call(client, "archive_template", {"id": template.id})["structuredContent"]["template"]
        assert archived["archived_at"] is not None
        template.refresh_from_db()
        assert template.archived_at is not None

        restored = call(client, "restore_template", {"id": template.id})["structuredContent"]["template"]
        assert restored["archived_at"] is None
        template.refresh_from_db()
        assert template.archived_at is None

    def test_archive_leaves_edit_time_alone(self, client, token, user):
        template = _template(user)
        updated_at = template.updated_at
        call(client, "archive_template", {"id": template.id})
        call(client, "restore_template", {"id": template.id})
        template.refresh_from_db()
        assert template.updated_at == updated_at


@pytest.mark.django_db
class TestScoping:
    def test_other_users_templates_are_invisible(self, client, token, other_user):
        template = _template(other_user)
        assert call(client, "list_templates", {"include_archived": True})["structuredContent"]["templates"] == []
        assert call(client, "get_template", {"id": template.id})["isError"] is True

    @pytest.mark.parametrize("tool", ["update_template", "archive_template", "restore_template"])
    def test_other_users_templates_cant_be_changed(self, client, token, other_user, tool):
        template = _template(other_user, title="Theirs")
        result = call(client, tool, {"id": template.id, **TEMPLATE})
        assert result["isError"] is True
        template.refresh_from_db()
        assert template.title == "Theirs"
        assert template.archived_at is None
        assert template.exercises.count() == 1

    def test_other_users_sessions_are_invisible(self, client, token, other_user):
        _ex(done_session(other_user), "Squat", [{"weight": 225, "reps": 5, "done": True}])
        assert call(client, "list_exercises")["structuredContent"]["exercises"] == []
        assert call(client, "get_sessions", {"start": "2026-08-01", "end": "2026-09-30"})["structuredContent"]["sessions"] == []
        assert call(client, "get_exercise_history", {"title": "Squat"})["structuredContent"]["total"] == 0

    def test_token_user_is_used(self, client, user, other_user):
        make_token(other_user, token="theirs")
        _template(user, title="Mine")
        response = post(client, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "list_templates", "arguments": {}}}, token="theirs")
        assert response.json()["result"]["structuredContent"]["templates"] == []

    def test_active_and_planned_sessions_never_show_up(self, client, token, user):
        for status in [Session.STATUS_ACTIVE, Session.STATUS_PLANNED]:
            session = Session.objects.create(title=status, date="2026-09-01", status=status, user=user)
            _ex(session, f"{status} lift", [{"weight": 100, "reps": 5, "done": True}])
        assert call(client, "list_exercises")["structuredContent"]["exercises"] == []
        assert call(client, "get_sessions", {"start": "2026-08-01", "end": "2026-09-30"})["structuredContent"]["sessions"] == []
        assert call(client, "get_exercise_history", {"title": "active lift"})["structuredContent"]["total"] == 0
