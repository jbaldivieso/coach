import datetime as dt
from collections import Counter
from datetime import date as DateType
from typing import List, Optional

from django.db import models, transaction
from django.utils import timezone
from ninja import Router, Schema
from ninja.security import django_auth

from accounts.api import MessageSchema

from .models import Exercise, Session

router = Router()


# ============ Schemas ============


class SetSchema(Schema):
    weight: Optional[float] = None  # None means bodyweight
    reps: int
    done: bool = True


class ExerciseSchema(Schema):
    id: int
    title: str
    sets: List[SetSchema]
    rest_seconds: int
    comments: str
    position: int
    superset_group: Optional[int] = None


class ExerciseCreateSchema(Schema):
    title: str
    sets: List[SetSchema]
    rest_seconds: int
    comments: str = ""
    position: Optional[int] = None
    superset_group: Optional[int] = None


class ExerciseUpsertSchema(ExerciseCreateSchema):
    """An exercise in a full-session save; id is set for exercises that already exist."""

    id: Optional[int] = None


class ExerciseUpdateSchema(Schema):
    title: Optional[str] = None
    sets: Optional[List[SetSchema]] = None
    rest_seconds: Optional[int] = None
    comments: Optional[str] = None
    position: Optional[int] = None
    superset_group: Optional[int] = None


class SessionSchema(Schema):
    id: int
    title: str
    date: DateType
    comments: str
    status: str
    started_at: Optional[dt.datetime] = None
    finished_at: Optional[dt.datetime] = None
    exercises: List[ExerciseSchema]


class SessionCreateSchema(Schema):
    title: str
    date: DateType
    comments: str = ""


class SessionUpdateSchema(Schema):
    title: Optional[str] = None
    date: Optional[DateType] = None
    comments: Optional[str] = None


class SessionWithExercisesCreateSchema(Schema):
    """Schema for creating a session with embedded exercises."""

    title: str
    date: DateType
    comments: str = ""
    status: str = Session.STATUS_DONE
    exercises: List[ExerciseCreateSchema]


class SessionWithExercisesUpdateSchema(Schema):
    """Schema for saving a whole session (planned or finished) from the editor."""

    title: str
    date: DateType
    comments: str = ""
    exercises: List[ExerciseUpsertSchema]


class SessionStartSchema(Schema):
    date: Optional[DateType] = None  # the client's local "today"


class SessionFinishSchema(Schema):
    comments: Optional[str] = None


class PaginatedSessionsSchema(Schema):
    """Schema for paginated sessions response."""

    items: List[SessionSchema]
    total: int
    has_more: bool


# ============ History and Search Schemas ============


class TitleSuggestionSchema(Schema):
    title: str
    count: int
    last_date: Optional[DateType] = None


class TitleSuggestionsSchema(Schema):
    suggestions: List[TitleSuggestionSchema]


class OutingSchema(Schema):
    """One done appearance of an exercise in a finished session."""

    exercise_id: int
    session_id: int
    session_title: str
    date: DateType
    sets: List[SetSchema]
    rest_seconds: int
    comments: str


class ExerciseHistorySchema(Schema):
    title: str
    items: List[OutingSchema]
    total: int
    has_more: bool


class SessionSummarySchema(Schema):
    id: int
    title: str
    date: DateType


class SearchResponseSchema(Schema):
    sessions: List[SessionSummarySchema]
    exercises: List[TitleSuggestionSchema]
    last_session: Optional[SessionSummarySchema] = None


# ============ Calendar Schemas ============


class SessionDateSchema(Schema):
    date: DateType
    session_id: int


class CalendarMonthSchema(Schema):
    year: int
    month: int
    sessions: List[SessionDateSchema]


class CalendarYearSchema(Schema):
    months: List[CalendarMonthSchema]


# ============ Helpers ============


def _fetch_session(session_id):
    return Session.objects.filter(id=session_id).prefetch_related("exercises").first()


def _parse_month(value: str):
    """Parse "YYYY-MM" into (year, month), or None if malformed."""
    try:
        year, month = (int(part) for part in value.split("-"))
    except ValueError:
        return None
    if not 1 <= month <= 12:
        return None
    return year, month


def _calendar_month(user, year: int, month: int):
    """Training dates in a month (planned sessions excluded), most recent session per date."""
    sessions = (
        Session.objects.filter(user=user, date__year=year, date__month=month)
        .exclude(status=Session.STATUS_PLANNED)
        .values("date")
        .annotate(session_id=models.Max("id"))
        .order_by("date")
    )
    return {
        "year": year,
        "month": month,
        "sessions": [{"date": s["date"], "session_id": s["session_id"]} for s in sessions],
    }


def _title_suggestions(queryset, limit: int):
    """Group a queryset of exercises or sessions by title with use count and last date, newest first."""
    date_field = "session__date" if queryset.model is Exercise else "date"
    rows = (
        queryset.values("title")
        .annotate(count=models.Count("id"), last_date=models.Max(date_field))
        .order_by("-last_date", "title")[:limit]
    )
    return [
        {"title": r["title"], "count": r["count"], "last_date": r["last_date"]}
        for r in rows
    ]


def _validate_date(date: DateType, status: str):
    if status != Session.STATUS_PLANNED and date > dt.date.today():
        return "Date cannot be in the future"
    return None


# ============ Session Endpoints ============


@router.get("/sessions/", response={200: PaginatedSessionsSchema, 400: MessageSchema}, auth=django_auth)
def list_sessions(
    request,
    offset: int = 0,
    limit: int = 10,
    status: str = Session.STATUS_DONE,
    month: Optional[str] = None,
):
    """List sessions for the authenticated user with pagination.

    Filters by status (default "done") and optionally by month ("YYYY-MM").
    """
    queryset = Session.objects.filter(user=request.user, status=status).prefetch_related(
        "exercises"
    )
    if month:
        parsed = _parse_month(month)
        if not parsed:
            return 400, {"message": "month must be YYYY-MM"}
        queryset = queryset.filter(date__year=parsed[0], date__month=parsed[1])
    total = queryset.count()
    sessions = queryset[offset : offset + limit]
    has_more = offset + limit < total
    return 200, {
        "items": sessions,
        "total": total,
        "has_more": has_more,
    }


@router.get("/sessions/open/", response=List[SessionSchema], auth=django_auth)
def list_open_sessions(request):
    """Planned and active sessions: active first, then planned by date."""
    sessions = (
        Session.objects.filter(
            user=request.user,
            status__in=[Session.STATUS_ACTIVE, Session.STATUS_PLANNED],
        )
        .prefetch_related("exercises")
        .order_by("status", "date", "id")  # "active" sorts before "planned"
    )
    return list(sessions)


@router.get("/sessions/autocomplete/", response=TitleSuggestionsSchema, auth=django_auth)
def session_title_autocomplete(request, q: str = ""):
    """Distinct session titles matching q, with use counts, most recent first."""
    if not q.strip():
        return {"suggestions": []}
    queryset = Session.objects.filter(user=request.user, title__icontains=q.strip())
    return {"suggestions": _title_suggestions(queryset, 8)}


@router.get("/sessions/calendar/", response=CalendarMonthSchema, auth=django_auth)
def get_calendar_month(request, year: int, month: int):
    """Get session dates for a given month. Returns most recent session per date."""
    return _calendar_month(request.user, year, month)


@router.get(
    "/sessions/calendar/year/",
    response={200: CalendarYearSchema, 400: MessageSchema},
    auth=django_auth,
)
def get_calendar_year(request, end: Optional[str] = None):
    """Training dates for the 12 months ending with `end` ("YYYY-MM", default this month)."""
    if end:
        parsed = _parse_month(end)
        if not parsed:
            return 400, {"message": "end must be YYYY-MM"}
        year, month = parsed
    else:
        today = dt.date.today()
        year, month = today.year, today.month

    months = []
    for _ in range(12):
        months.append(_calendar_month(request.user, year, month))
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    months.reverse()
    return 200, {"months": months}


@router.post(
    "/sessions/", response={201: SessionSchema, 400: MessageSchema}, auth=django_auth
)
def create_session(request, data: SessionCreateSchema):
    """Create a new lifting session."""
    session = Session.objects.create(user=request.user, **data.dict())
    return 201, session


@router.post(
    "/sessions/with-exercises/",
    response={201: SessionSchema, 400: MessageSchema},
    auth=django_auth,
)
def create_session_with_exercises(request, data: SessionWithExercisesCreateSchema):
    """Create a new lifting session with exercises in a single atomic operation.

    status may be "planned" (a future date is allowed), "active" (starts it now)
    or "done".
    """
    valid_statuses = [choice[0] for choice in Session.STATUS_CHOICES]
    if data.status not in valid_statuses:
        return 400, {
            "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        }

    date_error = _validate_date(data.date, data.status)
    if date_error:
        return 400, {"message": date_error}

    # Validate at least one exercise
    if not data.exercises:
        return 400, {"message": "At least one exercise is required"}

    # Use transaction to ensure atomicity
    with transaction.atomic():
        session = Session.objects.create(
            user=request.user,
            title=data.title,
            date=data.date,
            comments=data.comments,
            status=data.status,
            started_at=timezone.now() if data.status == Session.STATUS_ACTIVE else None,
        )

        for i, exercise_data in enumerate(data.exercises):
            exercise_dict = exercise_data.dict()
            exercise_dict["position"] = i
            Exercise.objects.create(session=session, **exercise_dict)

    return 201, _fetch_session(session.id)


@router.put(
    "/sessions/{session_id}/with-exercises/",
    response={200: SessionSchema, 400: MessageSchema, 404: MessageSchema},
    auth=django_auth,
)
def update_session_with_exercises(request, session_id: int, data: SessionWithExercisesUpdateSchema):
    """Save a whole session from the editor in one atomic operation.

    Exercises with an id are updated, those without are created, and any of the
    session's exercises missing from the payload are deleted. Order follows the
    payload.
    """
    session = Session.objects.filter(id=session_id, user=request.user).first()
    if not session:
        return 404, {"message": "Session not found"}

    date_error = _validate_date(data.date, session.status)
    if date_error:
        return 400, {"message": date_error}

    if not data.exercises:
        return 400, {"message": "At least one exercise is required"}

    existing = {e.id: e for e in session.exercises.all()}
    with transaction.atomic():
        session.title = data.title
        session.date = data.date
        session.comments = data.comments
        session.save()

        kept = set()
        for i, exercise_data in enumerate(data.exercises):
            exercise_dict = exercise_data.dict()
            exercise_id = exercise_dict.pop("id")
            exercise_dict["position"] = i
            exercise = existing.get(exercise_id)
            if exercise:
                for field, value in exercise_dict.items():
                    setattr(exercise, field, value)
                exercise.save()
                kept.add(exercise.id)
            else:
                Exercise.objects.create(session=session, **exercise_dict)

        Exercise.objects.filter(id__in=set(existing) - kept).delete()

    return 200, _fetch_session(session.id)


@router.get(
    "/sessions/{session_id}/",
    response={200: SessionSchema, 404: MessageSchema},
    auth=django_auth,
)
def get_session(request, session_id: int):
    """Get a specific session by ID."""
    session = (
        Session.objects.filter(id=session_id, user=request.user)
        .prefetch_related("exercises")
        .first()
    )
    if not session:
        return 404, {"message": "Session not found"}
    return 200, session


@router.put(
    "/sessions/{session_id}/",
    response={200: SessionSchema, 404: MessageSchema},
    auth=django_auth,
)
def update_session(request, session_id: int, data: SessionUpdateSchema):
    """Update a session."""
    session = Session.objects.filter(id=session_id, user=request.user).first()
    if not session:
        return 404, {"message": "Session not found"}

    for field, value in data.dict(exclude_unset=True).items():
        setattr(session, field, value)
    session.save()

    return 200, _fetch_session(session_id)


@router.post(
    "/sessions/{session_id}/start/",
    response={200: SessionSchema, 400: MessageSchema, 404: MessageSchema},
    auth=django_auth,
)
def start_session(request, session_id: int, data: SessionStartSchema):
    """Start a planned session: it becomes active and is dated today."""
    session = Session.objects.filter(id=session_id, user=request.user).first()
    if not session:
        return 404, {"message": "Session not found"}
    if session.status != Session.STATUS_PLANNED:
        return 400, {"message": "Only a planned session can be started"}

    session.status = Session.STATUS_ACTIVE
    session.started_at = timezone.now()
    session.date = data.date or dt.date.today()
    session.save()
    return 200, _fetch_session(session_id)


@router.post(
    "/sessions/{session_id}/finish/",
    response={200: SessionSchema, 400: MessageSchema, 404: MessageSchema},
    auth=django_auth,
)
def finish_session(request, session_id: int, data: SessionFinishSchema):
    """Finish an active session.

    Sets never marked done are dropped, exercises left with no sets are
    deleted, and superset groups left with one member are dissolved.
    """
    session = Session.objects.filter(id=session_id, user=request.user).first()
    if not session:
        return 404, {"message": "Session not found"}
    if session.status != Session.STATUS_ACTIVE:
        return 400, {"message": "Only an active session can be finished"}

    with transaction.atomic():
        remaining = []
        for exercise in session.exercises.all():
            done_sets = [s for s in exercise.sets if s.get("done")]
            if done_sets:
                exercise.sets = done_sets
                remaining.append(exercise)
            else:
                exercise.delete()

        group_sizes = Counter(e.superset_group for e in remaining if e.superset_group is not None)
        for i, exercise in enumerate(remaining):
            exercise.position = i
            if exercise.superset_group is not None and group_sizes[exercise.superset_group] < 2:
                exercise.superset_group = None
            exercise.save()

        if data.comments is not None:
            session.comments = data.comments
        session.status = Session.STATUS_DONE
        session.finished_at = timezone.now()
        session.save()

    return 200, _fetch_session(session_id)


@router.delete(
    "/sessions/{session_id}/",
    response={200: MessageSchema, 404: MessageSchema},
    auth=django_auth,
)
def delete_session(request, session_id: int):
    """Delete a session and all its exercises."""
    session = Session.objects.filter(id=session_id, user=request.user).first()
    if not session:
        return 404, {"message": "Session not found"}
    session.delete()
    return 200, {"message": "Session deleted"}


# ============ Exercise Endpoints ============


@router.post(
    "/sessions/{session_id}/exercises/",
    response={201: ExerciseSchema, 404: MessageSchema},
    auth=django_auth,
)
def create_exercise(request, session_id: int, data: ExerciseCreateSchema):
    """Create an exercise within a session."""
    session = Session.objects.filter(id=session_id, user=request.user).first()
    if not session:
        return 404, {"message": "Session not found"}

    exercise_dict = data.dict()
    with transaction.atomic():
        if exercise_dict.get("position") is None:
            # Append to the end
            max_position = Exercise.objects.filter(session=session).aggregate(
                max_pos=models.Max("position")
            )["max_pos"]
            exercise_dict["position"] = 0 if max_position is None else max_position + 1
        else:
            # Insert, shifting later exercises down
            Exercise.objects.filter(
                session=session, position__gte=exercise_dict["position"]
            ).update(position=models.F("position") + 1)

        exercise = Exercise.objects.create(session=session, **exercise_dict)
    return 201, exercise


@router.get("/exercises/autocomplete/", response=TitleSuggestionsSchema, auth=django_auth)
def exercise_title_autocomplete(request, q: str = "", limit: int = 8):
    """Distinct exercise titles from the user's history with use counts, most recent first.

    An empty query returns the most recently used titles.
    """
    queryset = Exercise.objects.filter(
        session__user=request.user, session__status=Session.STATUS_DONE
    )
    if q.strip():
        queryset = queryset.filter(title__icontains=q.strip())
    return {"suggestions": _title_suggestions(queryset, limit)}


@router.get("/exercises/history/", response=ExerciseHistorySchema, auth=django_auth)
def exercise_history(
    request,
    title: str,
    limit: int = 3,
    offset: int = 0,
    exclude_session: Optional[int] = None,
):
    """Done outings of an exercise (exact title match) in finished sessions, newest first."""
    queryset = (
        Exercise.objects.filter(
            session__user=request.user,
            session__status=Session.STATUS_DONE,
            title=title,
        )
        .select_related("session")
        .order_by("-session__date", "-session__id", "position")
    )
    if exclude_session is not None:
        queryset = queryset.exclude(session_id=exclude_session)

    total = queryset.count()
    items = [
        {
            "exercise_id": e.id,
            "session_id": e.session.id,
            "session_title": e.session.title,
            "date": e.session.date,
            "sets": [s for s in e.sets if s.get("done", True)],
            "rest_seconds": e.rest_seconds,
            "comments": e.comments,
        }
        for e in queryset[offset : offset + limit]
    ]
    return {
        "title": title,
        "items": items,
        "total": total,
        "has_more": offset + limit < total,
    }


@router.put(
    "/exercises/{exercise_id}/",
    response={200: ExerciseSchema, 404: MessageSchema},
    auth=django_auth,
)
def update_exercise(request, exercise_id: int, data: ExerciseUpdateSchema):
    """Update an exercise."""
    exercise = Exercise.objects.filter(
        id=exercise_id, session__user=request.user
    ).first()
    if not exercise:
        return 404, {"message": "Exercise not found"}

    for field, value in data.dict(exclude_unset=True).items():
        setattr(exercise, field, value)
    exercise.save()
    return 200, exercise


@router.delete(
    "/exercises/{exercise_id}/",
    response={200: MessageSchema, 404: MessageSchema},
    auth=django_auth,
)
def delete_exercise(request, exercise_id: int):
    """Delete an exercise."""
    exercise = Exercise.objects.filter(
        id=exercise_id, session__user=request.user
    ).first()
    if not exercise:
        return 404, {"message": "Exercise not found"}
    exercise.delete()
    return 200, {"message": "Exercise deleted"}


# ============ Search Endpoints ============


@router.get("/search/", response=SearchResponseSchema, auth=django_auth)
def search(request, q: str = ""):
    """Finished sessions and exercises whose titles match q.

    last_session is the most recent matching session, for "when did I last…"
    answers.
    """
    q = q.strip()
    if not q:
        return {"sessions": [], "exercises": [], "last_session": None}

    sessions = list(
        Session.objects.filter(
            user=request.user, status=Session.STATUS_DONE, title__icontains=q
        ).values("id", "title", "date")[:20]
    )
    exercises = _title_suggestions(
        Exercise.objects.filter(
            session__user=request.user,
            session__status=Session.STATUS_DONE,
            title__icontains=q,
        ),
        20,
    )
    return {
        "sessions": sessions,
        "exercises": exercises,
        "last_session": sessions[0] if sessions else None,
    }


# ============ Search Endpoints ============


# Legacy search, used by the old SearchView until it is rewritten on /search/.


class AutocompleteItemSchema(Schema):
    type: str  # "session" or "exercise"
    id: Optional[int]
    label: str
    value: str


class AutocompleteResponseSchema(Schema):
    items: List[AutocompleteItemSchema]


class SearchResultSchema(Schema):
    exercise_id: int
    exercise_title: str
    sets: List[SetSchema]
    rest_seconds: int
    session_id: int
    session_date: str
    session_title: str


class SearchResultsResponseSchema(Schema):
    items: List[SearchResultSchema]
    total: int


@router.get("/search/autocomplete/", response=AutocompleteResponseSchema, auth=django_auth)
def search_autocomplete(request, q: str = ""):
    """Return autocomplete suggestions for sessions and exercises."""
    if len(q) < 3:
        return {"items": []}

    items = []

    # Find distinct matching session titles
    session_titles = list(
        set(
            Session.objects.filter(
                user=request.user,
                title__icontains=q,
            ).values_list("title", flat=True)
        )
    )[:5]

    for title in session_titles:
        items.append({
            "type": "session",
            "id": None,
            "label": title,
            "value": title,
        })

    # Find distinct matching exercise titles
    exercise_titles = list(
        set(
            Exercise.objects.filter(
                session__user=request.user,
                title__icontains=q,
            ).values_list("title", flat=True)
        )
    )[:5]

    for title in exercise_titles:
        items.append({
            "type": "exercise",
            "id": None,
            "label": title,
            "value": title,
        })

    return {"items": items}


@router.get("/search/results/", response=SearchResultsResponseSchema, auth=django_auth)
def search_results(
    request,
    session_title: Optional[str] = None,
    exercise_title: Optional[str] = None,
):
    """Return search results filtered by session title and/or exercise title."""
    queryset = Exercise.objects.filter(session__user=request.user).select_related(
        "session"
    )

    if session_title:
        queryset = queryset.filter(session__title=session_title)

    if exercise_title:
        queryset = queryset.filter(title=exercise_title)

    # Order by session date descending, then exercise title
    queryset = queryset.order_by("-session__date", "title")

    items = []
    for exercise in queryset:
        items.append({
            "exercise_id": exercise.id,
            "exercise_title": exercise.title,
            "sets": exercise.sets,
            "rest_seconds": exercise.rest_seconds,
            "session_id": exercise.session.id,
            "session_date": str(exercise.session.date),
            "session_title": exercise.session.title,
        })

    return {"items": items, "total": len(items)}
