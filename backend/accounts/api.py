from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from ninja import Router, Schema
from ninja.security import django_auth

router = Router()


class LoginSchema(Schema):
    username: str
    password: str


class UserSchema(Schema):
    id: int
    username: str


class MessageSchema(Schema):
    message: str


class CSRFTokenSchema(Schema):
    csrf_token: str


@router.get("/csrf/", response=CSRFTokenSchema)
def get_csrf_token(request):
    """Get a CSRF token for making authenticated requests."""
    return {"csrf_token": get_token(request)}


@router.post("/login/", response={200: UserSchema, 401: MessageSchema})
def login_view(request, data: LoginSchema):
    """Authenticate a user and create a session."""
    user = authenticate(request, username=data.username, password=data.password)
    if user is not None:
        login(request, user)
        return 200, {"id": user.id, "username": user.username}
    return 401, {"message": "Invalid credentials"}


@router.post("/logout/", response=MessageSchema, auth=django_auth)
def logout_view(request):
    """Log out the current user."""
    logout(request)
    return {"message": "Logged out successfully"}


@router.get("/me/", response={200: UserSchema, 401: MessageSchema}, auth=django_auth)
def me(request):
    """Get the current authenticated user."""
    return 200, {"id": request.user.id, "username": request.user.username}
