"""
Delete clients that registered through /oauth/register/ but hold no live
connection. Registration is unauthenticated, and Claude registers a new client
each time the connector is added, so these pile up otherwise.

A client counts as unused once it's a day old and has no grant or refresh
token. Run it after cleartokens, which removes expired and rotated ones.

Usage:
    python manage.py clearoauthclients
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef
from django.utils import timezone
from oauth2_provider.models import get_application_model, get_grant_model, get_refresh_token_model

Application = get_application_model()


def unused_clients(now=None):
    now = now or timezone.now()
    in_use = Exists(get_grant_model().objects.filter(application=OuterRef("pk"))) | Exists(
        get_refresh_token_model().objects.filter(application=OuterRef("pk"))
    )
    return Application.objects.filter(
        registration_source=Application.RegistrationSource.DCR,
        created__lt=now - timedelta(days=1),
    ).exclude(in_use)


class Command(BaseCommand):
    help = "Delete dynamically registered OAuth clients with no live connection"

    def handle(self, *args, **options):
        clients = unused_clients()
        count = clients.count()
        clients.delete()
        self.stdout.write(f"Deleted {count} unused OAuth clients")
