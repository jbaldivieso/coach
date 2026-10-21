"""Template and history logic shared by the app API and the MCP tools."""

import difflib
import math

from django.db import transaction

from .models import Exercise, Session, Template, TemplateExercise

MAX_SETS = 6  # matches MAX_SETS in frontend/src/utils/plan.ts
MAX_TITLE = 100  # the models' max_length, which SQLite doesn't enforce
MAX_HISTORY = 50


class TemplateError(ValueError):
    """A template that can't be saved. The message says why, for the user or Claude."""


def _check_title(title, what):
    if not title.strip():
        raise TemplateError(f"{what} needs a title")
    if len(title) > MAX_TITLE:
        raise TemplateError(f"{what} title is over {MAX_TITLE} characters")


def _validate_template(data):
    _check_title(data.title, "The template")
    if not data.exercises:
        raise TemplateError("A template needs at least one exercise")

    for e in data.exercises:
        _check_title(e.title, "Every exercise")
        if e.rest_seconds < 0:
            raise TemplateError(f"{e.title}: rest can't be negative")
        if not 1 <= len(e.sets) <= MAX_SETS:
            raise TemplateError(f"{e.title} needs 1–{MAX_SETS} sets")
        for s in e.sets:
            if s.reps is not None and s.reps < 1:
                raise TemplateError(f"{e.title}: reps must be at least 1")
            if s.weight is not None and not math.isfinite(s.weight):
                raise TemplateError(f"{e.title}: weight must be a number")
            if s.weight is not None and s.weight < 0:
                raise TemplateError(f"{e.title}: weight can't be negative")

    groups = {}  # superset_group -> indexes of its exercises
    for i, e in enumerate(data.exercises):
        if e.superset_group is not None:
            groups.setdefault(e.superset_group, []).append(i)
    for indexes in groups.values():
        members = [data.exercises[i] for i in indexes]
        names = ", ".join(e.title for e in members)
        if indexes != list(range(indexes[0], indexes[-1] + 1)):
            raise TemplateError(f"Superset exercises must be adjacent ({names})")
        if len(indexes) != 2:
            raise TemplateError(f"A superset is exactly 2 exercises ({names})")
        if len({len(e.sets) for e in members}) > 1:
            raise TemplateError(f"Superset exercises need the same number of sets ({names})")


def save_template(user, data, template=None):
    """Create a template, or replace an existing one's fields and exercises.

    data is a TemplateInputSchema. Returns (template, warnings), where warnings
    flag exercise titles that aren't in the user's history. Raises
    TemplateError, changing nothing, when the template is invalid.
    """
    _validate_template(data)

    with transaction.atomic():
        if template is None:
            template = Template(user=user)
        template.title = data.title
        template.comments = data.comments
        template.save()

        template.exercises.all().delete()
        for i, e in enumerate(data.exercises):
            TemplateExercise.objects.create(
                template=template,
                title=e.title,
                sets=[s.dict() for s in e.sets],
                rest_seconds=e.rest_seconds,
                comments=e.comments,
                position=i,
                superset_group=e.superset_group,
            )

    warnings = unknown_title_warnings(user, [e.title for e in data.exercises])
    return template, warnings


def unknown_title_warnings(user, titles):
    """One warning per title that isn't in the user's finished sessions, with close matches."""
    known = list(
        Exercise.objects.filter(session__user=user, session__status=Session.STATUS_DONE)
        .values_list("title", flat=True)
        .distinct()
    )
    warnings = []
    for title in dict.fromkeys(titles):
        if title in known:
            continue
        matches = difflib.get_close_matches(title, known)
        warning = f'"{title}" isn\'t in your history.'
        if matches:
            warning += " Close matches: " + ", ".join(f'"{m}"' for m in matches) + "."
        warnings.append(warning)
    return warnings


def exercise_history(user, title, limit, offset, exclude_session=None):
    """Done outings of an exercise (exact title match) in finished sessions, newest first."""
    limit = min(max(limit, 1), MAX_HISTORY)
    offset = max(offset, 0)
    queryset = (
        Exercise.objects.filter(
            session__user=user,
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
