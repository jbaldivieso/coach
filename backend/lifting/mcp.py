"""The Coach MCP server, for the Claude connector.

MCP's Streamable HTTP transport in stateless mode with JSON responses: one
JSON-RPC message per POST, no SSE and no Mcp-Session-Id. That's small enough to
serve from a plain Django view in the existing worker. Every request carries an
OAuth access token (see accounts.oauth), and the token's user scopes every
query.
"""

import datetime as dt
import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.common import no_append_slash
from django.views.decorators.csrf import csrf_exempt
from ninja import Field, Schema
from oauth2_provider.oauth2_backends import get_oauthlib_core
from pydantic import ValidationError

from . import services
from .api import (
    ExerciseHistorySchema,
    SessionSchema,
    TemplateInputSchema,
    TemplateSchema,
    TitleSuggestionSchema,
    _title_suggestions,
)
from .models import Exercise, Session, Template

logger = logging.getLogger(__name__)

PROTOCOL_VERSIONS = ["2025-11-25", "2025-06-18", "2025-03-26"]  # newest first
MAX_SESSION_DAYS = 180

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

INSTRUCTIONS = """\
Coach is a lifting log. You can read the lifter's finished sessions and create, \
edit, archive and restore their workout templates. Templates show up in the app \
under "Start from…", and starting one copies it into a new session.

- Weights are in lb. A null weight means bodyweight.
- Each set carries its own weight and reps.
- A superset is exactly 2 adjacent exercises sharing a superset_group, with the \
same number of sets. The lifter does one set of each back to back, then rests \
once: there's no rest between the two, and only the first exercise's \
rest_seconds counts. An exercise has at most 6 sets.
- Exercise titles are the history key. Reuse the exact titles from \
list_exercises, or the new exercise won't connect to its history.
- In a template, a set's weight and reps are both optional. Leave them blank, \
or describe the prescription in the exercise comments, when the lifter should \
choose on the day.
- Template comments become the session note, and exercise comments carry into \
the session's exercise comments, where the lifter deletes them.
"""


# ============ Tool arguments ============


class ExerciseSummarySchema(TitleSuggestionSchema):
    first_date: dt.date


class NoArgs(Schema):
    pass


class GetSessionsArgs(Schema):
    start: dt.date = Field(description="First date, inclusive (YYYY-MM-DD)")
    end: dt.date = Field(description=f"Last date, inclusive. At most {MAX_SESSION_DAYS} days after start")


class GetExerciseHistoryArgs(Schema):
    title: str = Field(description="Exact exercise title, as list_exercises gives it")
    limit: int = Field(10, json_schema_extra={"minimum": 1, "maximum": services.MAX_HISTORY})
    offset: int = Field(0, json_schema_extra={"minimum": 0})


class ListTemplatesArgs(Schema):
    include_archived: bool = False


class TemplateIdArgs(Schema):
    id: int


class UpdateTemplateArgs(TemplateInputSchema):
    id: int


# ============ Tools ============


class ToolError(Exception):
    """A tool failure Claude can fix and retry, returned as an isError result."""


def _template_json(template):
    return TemplateSchema.from_orm(template).model_dump(mode="json")


def _own_templates(user, template_id):
    templates = Template.objects.filter(id=template_id, user=user)
    if not templates.exists():
        raise ToolError(f"Template {template_id} not found")
    return templates


def _own_template(user, template_id):
    return _own_templates(user, template_id).prefetch_related("exercises").get()


def list_exercises(user, args):
    rows = _title_suggestions(
        Exercise.objects.filter(session__user=user, session__status=Session.STATUS_DONE)
    )
    return {"exercises": [ExerciseSummarySchema(**r).model_dump(mode="json") for r in rows]}


def get_sessions(user, args):
    if args.end < args.start:
        raise ToolError("end is before start")
    if (args.end - args.start).days > MAX_SESSION_DAYS:
        raise ToolError(f"Ask for at most {MAX_SESSION_DAYS} days at a time")
    sessions = (
        Session.objects.filter(
            user=user, status=Session.STATUS_DONE, date__gte=args.start, date__lte=args.end
        )
        .prefetch_related("exercises")
        .order_by("date", "id")
    )
    return {"sessions": [SessionSchema.from_orm(s).model_dump(mode="json") for s in sessions]}


def get_exercise_history(user, args):
    history = services.exercise_history(user, args.title, args.limit, args.offset)
    return ExerciseHistorySchema(**history).model_dump(mode="json")


def list_templates(user, args):
    templates = Template.objects.filter(user=user).prefetch_related("exercises")
    if not args.include_archived:
        templates = templates.filter(archived_at__isnull=True)
    return {"templates": [_template_json(t) for t in templates]}


def get_template(user, args):
    return {"template": _template_json(_own_template(user, args.id))}


def _save(user, data, template=None):
    try:
        template, warnings = services.save_template(user, data, template)
    except services.TemplateError as e:
        raise ToolError(str(e))
    return {"template": _template_json(_own_template(user, template.id)), "warnings": warnings}


def create_template(user, args):
    return _save(user, args)


def update_template(user, args):
    return _save(user, args, _own_templates(user, args.id).get())


def _set_archived(user, template_id, archived_at):
    # update() rather than save(): it leaves the other columns and updated_at
    # alone, so archiving doesn't reorder the list or undo a concurrent edit
    templates = _own_templates(user, template_id)
    if archived_at is None:
        templates.filter(archived_at__isnull=False).update(archived_at=None)
    else:
        templates.filter(archived_at__isnull=True).update(archived_at=archived_at)
    return {"template": _template_json(_own_template(user, template_id))}


def archive_template(user, args):
    return _set_archived(user, args.id, timezone.now())


def restore_template(user, args):
    return _set_archived(user, args.id, None)


# Tool annotations, which tell the client which tools need the lifter's approval
READ = {"readOnlyHint": True, "openWorldHint": False}
CREATE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
REPLACE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}
TOGGLE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

TOOLS = {
    "list_exercises": (
        "Every exercise title in the lifter's finished sessions, with how many times it was done "
        "and the first and last dates. Match exercise names against these titles.",
        NoArgs,
        list_exercises,
        READ,
    ),
    "get_sessions": (
        f"Finished sessions dated start to end (inclusive, at most {MAX_SESSION_DAYS} days), "
        "oldest first, in full: exercises, done sets (weight in lb, null for bodyweight), rest, "
        "comments, and the template_id each was started from.",
        GetSessionsArgs,
        get_sessions,
        READ,
    ),
    "get_exercise_history": (
        "Past outings of one exercise (exact title) in finished sessions, newest first, with "
        "their sets, rest and comments. Page with limit and offset.",
        GetExerciseHistoryArgs,
        get_exercise_history,
        READ,
    ),
    "list_templates": (
        "The lifter's workout templates with their exercises, most recently edited first. "
        "Archived templates are left out unless include_archived is true.",
        ListTemplatesArgs,
        list_templates,
        READ,
    ),
    "get_template": ("One workout template with its exercises.", TemplateIdArgs, get_template, READ),
    "create_template": (
        "Create a workout template. Set weight (lb) and reps are optional. Returns the template "
        "and warnings for exercise titles that aren't in the lifter's history.",
        TemplateInputSchema,
        create_template,
        CREATE,
    ),
    "update_template": (
        "Replace a template's title, comments and exercises in full. Past sessions started from "
        "it don't change. Returns the template and warnings, as create_template does.",
        UpdateTemplateArgs,
        update_template,
        REPLACE,
    ),
    "archive_template": (
        "Archive a template, which takes it off the app's list. It can be restored.",
        TemplateIdArgs,
        archive_template,
        TOGGLE,
    ),
    "restore_template": (
        "Restore an archived template to the app's list.",
        TemplateIdArgs,
        restore_template,
        TOGGLE,
    ),
}


# ============ JSON-RPC ============


class RpcError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _tool_result(data, is_error=False):
    if is_error:
        return {"content": [{"type": "text", "text": data}], "isError": True}
    return {"content": [{"type": "text", "text": json.dumps(data)}], "structuredContent": data}


def _initialize(user, params):
    requested = params.get("protocolVersion")
    return {
        "protocolVersion": requested if requested in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "coach", "version": "1.0.0"},
        "instructions": INSTRUCTIONS,
    }


TOOLS_LIST = {
    "tools": [
        {
            "name": name,
            "description": description,
            "inputSchema": args.model_json_schema(),
            "annotations": annotations,
        }
        for name, (description, args, _, annotations) in TOOLS.items()
    ]
}


def _tools_list(user, params):
    return TOOLS_LIST


def _tools_call(user, params):
    name = params.get("name")
    if not isinstance(name, str) or name not in TOOLS:
        raise RpcError(INVALID_PARAMS, f"Unknown tool: {name}")
    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise RpcError(INVALID_PARAMS, "arguments must be an object")

    _, args_schema, tool, _ = TOOLS[name]
    try:
        args = args_schema(**arguments)
    except ValidationError as e:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in e.errors()
        )
        return _tool_result(f"Invalid arguments: {problems}", is_error=True)
    try:
        return _tool_result(tool(user, args))
    except ToolError as e:
        return _tool_result(str(e), is_error=True)


METHODS = {
    "initialize": _initialize,
    "ping": lambda user, params: {},
    "tools/list": _tools_list,
    "tools/call": _tools_call,
}


def _error(id, code, message, status=200):
    return JsonResponse(
        {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}, status=status
    )


def _token_user(request):
    """The access token's user, or None and the OAuth error.

    The token must be issued for this server and have the coach scope.
    """
    # Checked against the public resource URL rather than one built from the
    # Host header, which is what the token's audience has to match. Scopes are
    # checked here rather than by verify_request, so that a token without the
    # coach scope gets insufficient_scope instead of looking expired.
    valid, r = get_oauthlib_core().server.verify_request(
        f"{settings.COACH_PUBLIC_URL}/mcp",
        "POST",
        headers={"Authorization": request.headers.get("Authorization", "")},
        scopes=[],
    )
    # DOT skips the audience check for tokens issued without a resource
    # indicator, so those are refused here
    if not valid or not r.access_token.resource or r.user is None or not r.user.is_active:
        return None, "invalid_token"
    if not r.access_token.allow_scopes(["coach"]):
        return None, "insufficient_scope"
    return r.user, None


@csrf_exempt
@no_append_slash
def mcp_view(request):
    if request.method != "POST":
        return HttpResponse(status=405, headers={"Allow": "POST"})

    user, auth_error = _token_user(request)
    if user is None:
        metadata = f"{settings.COACH_PUBLIC_URL}/.well-known/oauth-protected-resource"
        challenge = f'Bearer resource_metadata="{metadata}"'
        status = 401
        if auth_error == "insufficient_scope":
            challenge = f'Bearer error="insufficient_scope", scope="coach", resource_metadata="{metadata}"'
            status = 403
        return JsonResponse({"error": auth_error}, status=status, headers={"WWW-Authenticate": challenge})

    try:
        message = json.loads(request.body)
    except ValueError:
        return _error(None, PARSE_ERROR, "Parse error", status=400)
    if isinstance(message, list):
        return _error(None, INVALID_REQUEST, "Batches aren't supported", status=400)
    if not isinstance(message, dict):
        return _error(None, INVALID_REQUEST, "Expected a JSON-RPC message", status=400)

    if "method" not in message or "id" not in message:
        # A notification, or a response to a request we never send
        return HttpResponse(status=202)

    id = message["id"]
    if not isinstance(message["method"], str):
        return _error(id, INVALID_REQUEST, "method must be a string")
    method = METHODS.get(message["method"])
    if method is None:
        return _error(id, METHOD_NOT_FOUND, f"Method not found: {message['method']}")
    params = message.get("params") or {}
    if not isinstance(params, dict):
        return _error(id, INVALID_PARAMS, "params must be an object")
    try:
        result = method(user, params)
    except RpcError as e:
        return _error(id, e.code, e.message)
    except Exception:
        logger.exception("MCP %s failed", message["method"])
        return _error(id, INTERNAL_ERROR, "Internal error")
    return JsonResponse({"jsonrpc": "2.0", "id": id, "result": result})
