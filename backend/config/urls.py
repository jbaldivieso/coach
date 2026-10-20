"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.conf import settings
from oauth2_provider import urls as oauth2_urls
from oauth2_provider import views as oauth2_views

from accounts import oauth
from lifting import mcp

from .api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    # No trailing slash: the URL must equal the OAuth metadata's resource exactly
    path("mcp", mcp.mcp_view, name="mcp"),
    # Only these from DOT: its full include also mounts application management
    # (any user could register a client), OIDC and device-flow routes. They
    # stay in DOT's namespace because its metadata view reverses them.
    path("", include((oauth2_urls.metadata_urlpatterns + [
        path("oauth/authorize/", oauth.AuthorizationView.as_view(), name="authorize"),
        path("oauth/token/", oauth2_views.TokenView.as_view(), name="token"),
        path("oauth/revoke_token/", oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
        path("oauth/register/", oauth.RegistrationView.as_view(), name="dcr-register"),
        path(
            "oauth/register/<str:client_id>/",
            oauth.RegistrationManagementView.as_view(),
            name="dcr-register-management",
        ),
    ], "oauth2_provider"))),
]

# In production (DEBUG=False), serve the Vue SPA for all non-API routes
if not settings.DEBUG:
    urlpatterns += [
        re_path(r"^(?!api/|admin/|static/|oauth/|mcp(?:/|$)|\.well-known/).*$", TemplateView.as_view(template_name="index.html")),
    ]
