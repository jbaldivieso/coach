"""OAuth for the Claude connector.

django-oauth-toolkit provides every endpoint, including the discovery
documents Claude reads first (RFC 9728, RFC 8414) and dynamic client
registration (RFC 7591), all configured in settings.OAUTH2_PROVIDER. These
subclasses limit registration to Claude's callbacks, so anyone can register
but only Claude can receive the codes.
"""

import json
from urllib.parse import urlparse

from django.http import JsonResponse
from oauth2_provider.views import AuthorizationView as BaseAuthorizationView
from oauth2_provider.views.dynamic_client_registration import (
    DynamicClientRegistrationManagementView,
    DynamicClientRegistrationView,
)

ALLOWED_REDIRECT_URIS = {
    "https://claude.ai/api/mcp/auth_callback",
    "https://claude.com/api/mcp/auth_callback",
}


def refuse_other_redirect_uris(body):
    """An invalid_redirect_uri response, or None to let DOT handle the request.

    Bodies that aren't a JSON object pass through, so DOT reports them.
    """
    try:
        data = json.loads(body)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    uris = data.get("redirect_uris")
    if (
        isinstance(uris, list)
        and uris
        and all(isinstance(uri, str) and uri in ALLOWED_REDIRECT_URIS for uri in uris)
    ):
        return None
    return JsonResponse(
        {"error": "invalid_redirect_uri", "error_description": "Only Claude's callback URLs can be registered."},
        status=400,
    )


class RegistrationView(DynamicClientRegistrationView):
    def post(self, request, *args, **kwargs):
        return refuse_other_redirect_uris(request.body) or super().post(request, *args, **kwargs)


class RegistrationManagementView(DynamicClientRegistrationManagementView):
    """RFC 7592 read, update and delete, with the same limit on updates."""

    def put(self, request, *args, **kwargs):
        return refuse_other_redirect_uris(request.body) or super().put(request, *args, **kwargs)


class AuthorizationView(BaseAuthorizationView):
    """DOT's consent view, plus the redirect hostname for the consent screen."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["redirect_host"] = urlparse(context.get("redirect_uri") or "").hostname
        return context
