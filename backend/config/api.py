from ninja import NinjaAPI
from ninja.security import django_auth

from accounts.api import router as accounts_router
from lifting.api import router as lifting_router

api = NinjaAPI(
    title="Coach API",
    version="1.0.0",
)

api.add_router("/accounts/", accounts_router, tags=["accounts"])
api.add_router("/lifting/", lifting_router, tags=["lifting"])


@api.get("/health/")
def health_check(request):
    """Health check endpoint."""
    return {"status": "ok"}
