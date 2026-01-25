"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView
from django.conf import settings

from .api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

# In production (DEBUG=False), serve the Vue SPA for all non-API routes
if not settings.DEBUG:
    urlpatterns += [
        re_path(r"^(?!api/|admin/|static/).*$", TemplateView.as_view(template_name="index.html")),
    ]
