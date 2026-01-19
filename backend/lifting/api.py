from datetime import date as DateType
from typing import List, Optional

from django.db import transaction
from ninja import Router, Schema
from ninja.security import django_auth

from accounts.api import MessageSchema
from .models import Session, Exercise


router = Router()


# ============ Schemas ============

class ExerciseSchema(Schema):
    id: int
    title: str
    weight_lbs: Optional[int]
    rest_seconds: int
    reps: List[int]
    comments: str


class ExerciseCreateSchema(Schema):
    title: str
    weight_lbs: Optional[int] = None
    rest_seconds: int
    reps: List[int]
    comments: str = ""


class ExerciseUpdateSchema(Schema):
    title: Optional[str] = None
    weight_lbs: Optional[int] = None
    rest_seconds: Optional[int] = None
    reps: Optional[List[int]] = None
    comments: Optional[str] = None


class SessionSchema(Schema):
    id: int
    title: str
    date: DateType
    comments: str
    session_type: str
    exercises: List[ExerciseSchema]


class SessionCreateSchema(Schema):
    title: str
    date: DateType
    comments: str = ""
    session_type: str


class SessionUpdateSchema(Schema):
    title: Optional[str] = None
    date: Optional[DateType] = None
    comments: Optional[str] = None
    session_type: Optional[str] = None


class SessionWithExercisesCreateSchema(Schema):
    """Schema for creating a session with embedded exercises."""
    title: str
    date: DateType
    comments: str = ""
    session_type: str
    exercises: List[ExerciseCreateSchema]


class PaginatedSessionsSchema(Schema):
    """Schema for paginated sessions response."""
    items: List[SessionSchema]
    total: int
    has_more: bool


# ============ Session Endpoints ============

@router.get("/sessions/", response=PaginatedSessionsSchema, auth=django_auth)
def list_sessions(request, offset: int = 0, limit: int = 10):
    """List sessions for the authenticated user with pagination."""
    queryset = Session.objects.filter(user=request.user).prefetch_related("exercises")
    total = queryset.count()
    sessions = queryset[offset:offset + limit]
    has_more = offset + limit < total
    return {
        "items": sessions,
        "total": total,
        "has_more": has_more,
    }


@router.post("/sessions/", response={201: SessionSchema, 400: MessageSchema}, auth=django_auth)
def create_session(request, data: SessionCreateSchema):
    """Create a new lifting session."""
    session = Session.objects.create(user=request.user, **data.dict())
    return 201, session


@router.post("/sessions/with-exercises/", response={201: SessionSchema, 400: MessageSchema}, auth=django_auth)
def create_session_with_exercises(request, data: SessionWithExercisesCreateSchema):
    """Create a new lifting session with exercises in a single atomic operation."""
    # Validate session_type
    valid_types = [choice[0] for choice in Session.SESSION_TYPE_CHOICES]
    if data.session_type not in valid_types:
        return 400, {"message": f"Invalid session type. Must be one of: {', '.join(valid_types)}"}

    # Validate date is not in future
    if data.date > date.today():
        return 400, {"message": "Date cannot be in the future"}

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
            session_type=data.session_type,
        )

        for exercise_data in data.exercises:
            Exercise.objects.create(
                session=session,
                **exercise_data.dict()
            )

    # Refetch with exercises for response
    session = Session.objects.filter(id=session.id).prefetch_related("exercises").first()
    return 201, session


@router.get("/sessions/{session_id}/", response={200: SessionSchema, 404: MessageSchema}, auth=django_auth)
def get_session(request, session_id: int):
    """Get a specific session by ID."""
    session = Session.objects.filter(id=session_id, user=request.user).prefetch_related("exercises").first()
    if not session:
        return 404, {"message": "Session not found"}
    return 200, session


@router.put("/sessions/{session_id}/", response={200: SessionSchema, 404: MessageSchema}, auth=django_auth)
def update_session(request, session_id: int, data: SessionUpdateSchema):
    """Update a session."""
    session = Session.objects.filter(id=session_id, user=request.user).first()
    if not session:
        return 404, {"message": "Session not found"}

    for field, value in data.dict(exclude_unset=True).items():
        setattr(session, field, value)
    session.save()

    # Refetch with exercises for response
    session = Session.objects.filter(id=session_id).prefetch_related("exercises").first()
    return 200, session


@router.delete("/sessions/{session_id}/", response={200: MessageSchema, 404: MessageSchema}, auth=django_auth)
def delete_session(request, session_id: int):
    """Delete a session and all its exercises."""
    session = Session.objects.filter(id=session_id, user=request.user).first()
    if not session:
        return 404, {"message": "Session not found"}
    session.delete()
    return 200, {"message": "Session deleted"}


# ============ Exercise Endpoints ============

@router.post("/sessions/{session_id}/exercises/", response={201: ExerciseSchema, 404: MessageSchema}, auth=django_auth)
def create_exercise(request, session_id: int, data: ExerciseCreateSchema):
    """Create an exercise within a session."""
    session = Session.objects.filter(id=session_id, user=request.user).first()
    if not session:
        return 404, {"message": "Session not found"}

    exercise = Exercise.objects.create(session=session, **data.dict())
    return 201, exercise


@router.put("/exercises/{exercise_id}/", response={200: ExerciseSchema, 404: MessageSchema}, auth=django_auth)
def update_exercise(request, exercise_id: int, data: ExerciseUpdateSchema):
    """Update an exercise."""
    exercise = Exercise.objects.filter(id=exercise_id, session__user=request.user).first()
    if not exercise:
        return 404, {"message": "Exercise not found"}

    for field, value in data.dict(exclude_unset=True).items():
        setattr(exercise, field, value)
    exercise.save()
    return 200, exercise


@router.delete("/exercises/{exercise_id}/", response={200: MessageSchema, 404: MessageSchema}, auth=django_auth)
def delete_exercise(request, exercise_id: int):
    """Delete an exercise."""
    exercise = Exercise.objects.filter(id=exercise_id, session__user=request.user).first()
    if not exercise:
        return 404, {"message": "Exercise not found"}
    exercise.delete()
    return 200, {"message": "Exercise deleted"}
