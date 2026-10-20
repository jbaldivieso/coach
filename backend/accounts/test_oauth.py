import base64
import hashlib
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from oauth2_provider.models import Application, Grant, RefreshToken

CLAUDE_CALLBACK = "https://claude.ai/api/mcp/auth_callback"
VERIFIER = "a-long-enough-pkce-code-verifier-for-the-tests-0123456789"
CHALLENGE = base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).rstrip(b"=").decode()


def origin():
    return settings.COACH_PUBLIC_URL


def register(client, **overrides):
    body = {
        "client_name": "Claude",
        "redirect_uris": [CLAUDE_CALLBACK],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        **overrides,
    }
    return client.post("/oauth/register/", data=body, content_type="application/json")


def authorize_params(client_id):
    return {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": CLAUDE_CALLBACK,
        "code_challenge": CHALLENGE,
        "code_challenge_method": "S256",
        "state": "xyz",
        "scope": "coach",
        "resource": f"{origin()}/mcp",
    }


class TestMetadata:
    @pytest.mark.parametrize("path", ["/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"])
    def test_protected_resource(self, client, path):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {
            "resource": f"{origin()}/mcp",
            "authorization_servers": [origin()],
            "scopes_supported": ["coach"],
            "bearer_methods_supported": ["header"],
        }
        assert response["Access-Control-Allow-Origin"] == "*"

    def test_authorization_server(self, client):
        response = client.get("/.well-known/oauth-authorization-server")
        assert response.status_code == 200
        data = response.json()
        assert data["issuer"] == origin()
        assert data["authorization_endpoint"] == f"{origin()}/oauth/authorize/"
        assert data["token_endpoint"] == f"{origin()}/oauth/token/"
        assert data["registration_endpoint"] == f"{origin()}/oauth/register/"
        assert data["revocation_endpoint"] == f"{origin()}/oauth/revoke_token/"
        assert data["response_types_supported"] == ["code"]
        assert data["grant_types_supported"] == ["authorization_code", "refresh_token"]
        assert data["code_challenge_methods_supported"] == ["S256"]
        assert data["token_endpoint_auth_methods_supported"] == ["none"]
        assert data["scopes_supported"] == ["coach"]
        assert data["client_id_metadata_document_supported"] is False
        assert response["Access-Control-Allow-Origin"] == "*"


@pytest.mark.django_db
class TestRegistration:
    @pytest.mark.parametrize("uri", [CLAUDE_CALLBACK, "https://claude.com/api/mcp/auth_callback"])
    def test_allowlisted_redirect_uri_creates_public_client(self, client, uri):
        response = register(client, redirect_uris=[uri])
        assert response.status_code == 201
        data = response.json()
        assert data["redirect_uris"] == [uri]
        assert data["token_endpoint_auth_method"] == "none"
        assert data["grant_types"] == ["authorization_code", "refresh_token"]
        assert "client_secret" not in data

        app = Application.objects.get(client_id=data["client_id"])
        assert app.client_type == Application.CLIENT_PUBLIC
        assert app.authorization_grant_type == Application.GRANT_AUTHORIZATION_CODE
        assert app.redirect_uris == uri
        assert app.user is None

    @pytest.mark.parametrize(
        "uris",
        [
            ["https://evil.example/api/mcp/auth_callback"],
            [CLAUDE_CALLBACK, "https://evil.example/cb"],
            ["https://claude.ai/api/mcp/auth_callback/../x"],
            [],
            [[CLAUDE_CALLBACK]],
            [{}],
            CLAUDE_CALLBACK,
            None,
        ],
    )
    def test_other_redirect_uri_is_refused(self, client, uris):
        response = register(client, redirect_uris=uris)
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_redirect_uri"
        assert not Application.objects.exists()

    def test_bad_json_is_refused(self, client):
        response = client.post("/oauth/register/", data="{", content_type="application/json")
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_client_metadata"

    def test_update_to_other_redirect_uri_is_refused(self, client):
        data = register(client).json()
        response = client.put(
            f"/oauth/register/{data['client_id']}/",
            data={"redirect_uris": ["https://evil.example/cb"], "token_endpoint_auth_method": "none"},
            content_type="application/json",
            headers={"Authorization": f"Bearer {data['registration_access_token']}"},
        )
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_redirect_uri"
        assert Application.objects.get().redirect_uris == CLAUDE_CALLBACK

    def test_get_is_not_allowed(self, client):
        assert client.get("/oauth/register/").status_code == 405

    @pytest.mark.parametrize(
        "path", ["/oauth/applications/register/", "/oauth/userinfo/", "/oauth/device/", "/oauth/introspect/"]
    )
    def test_other_dot_routes_are_not_mounted(self, admin_client, path):
        assert admin_client.get(path).status_code == 404


@pytest.mark.django_db
class TestAuthorizationFlow:
    def test_anonymous_user_is_sent_to_login(self, client):
        client_id = register(client).json()["client_id"]
        response = client.get("/oauth/authorize/", authorize_params(client_id))
        assert response.status_code == 302
        target = urlparse(response["Location"])
        assert target.path == "/login"
        assert parse_qs(target.query)["next"][0].startswith("/oauth/authorize/?")

    def test_consent_screen_names_claude_and_the_redirect_host(self, client, user):
        client_id = register(client).json()["client_id"]
        client.login(username="testuser", password="testpass123")
        response = client.get("/oauth/authorize/", authorize_params(client_id))
        assert response.status_code == 200
        html = response.content.decode()
        assert "wants to read your lifting history and manage your templates" in html
        assert "claude.ai" in html
        assert 'name="allow"' in html

    def test_deny_returns_access_denied(self, client, user):
        client_id = register(client).json()["client_id"]
        client.login(username="testuser", password="testpass123")
        response = client.post("/oauth/authorize/", authorize_params(client_id))
        assert response.status_code == 302
        assert parse_qs(urlparse(response["Location"]).query)["error"] == ["access_denied"]

    def test_full_flow_with_rotating_refresh(self, client, user):
        client_id = register(client).json()["client_id"]
        client.login(username="testuser", password="testpass123")

        response = client.post("/oauth/authorize/", {**authorize_params(client_id), "allow": "Allow"})
        assert response.status_code == 302
        redirect = urlparse(response["Location"])
        assert f"{redirect.scheme}://{redirect.netloc}{redirect.path}" == CLAUDE_CALLBACK
        query = parse_qs(redirect.query)
        assert query["state"] == ["xyz"]
        code = query["code"][0]

        client.logout()  # the token endpoint is machine-to-machine
        token = client.post(
            "/oauth/token/",
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": CLAUDE_CALLBACK,
                "client_id": client_id,
                "code_verifier": VERIFIER,
                "resource": f"{origin()}/mcp",
            },
        )
        assert token.status_code == 200, token.content
        tokens = token.json()
        assert tokens["token_type"] == "Bearer"
        assert tokens["expires_in"] == 3600
        assert tokens["scope"] == "coach"

        refreshed = client.post(
            "/oauth/token/",
            {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"], "client_id": client_id},
        )
        assert refreshed.status_code == 200, refreshed.content
        assert refreshed.json()["refresh_token"] != tokens["refresh_token"]

        # A retry inside the grace period still works
        retried = client.post(
            "/oauth/token/",
            {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"], "client_id": client_id},
        )
        assert retried.status_code == 200, retried.content

        RefreshToken.objects.filter(token=tokens["refresh_token"]).update(
            revoked=timezone.now() - timedelta(seconds=121)
        )
        stale = client.post(
            "/oauth/token/",
            {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"], "client_id": client_id},
        )
        assert stale.status_code == 400
        assert stale.json()["error"] == "invalid_grant"

    def test_wrong_verifier_is_refused(self, client, user):
        client_id = register(client).json()["client_id"]
        client.login(username="testuser", password="testpass123")
        response = client.post("/oauth/authorize/", {**authorize_params(client_id), "allow": "Allow"})
        code = parse_qs(urlparse(response["Location"]).query)["code"][0]
        token = client.post(
            "/oauth/token/",
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": CLAUDE_CALLBACK,
                "client_id": client_id,
                "code_verifier": "x" * 50,
            },
        )
        assert token.status_code == 400
        assert token.json()["error"] == "invalid_grant"


@pytest.mark.django_db
class TestClearOAuthClients:
    def age(self, app, days):
        Application.objects.filter(pk=app.pk).update(created=timezone.now() - timedelta(days=days))

    def test_deletes_old_unused_registrations_only(self, client, user):
        unused = Application.objects.get(client_id=register(client).json()["client_id"])
        fresh = Application.objects.get(client_id=register(client).json()["client_id"])
        connected = Application.objects.get(client_id=register(client).json()["client_id"])
        manual = Application.objects.create(
            name="Admin-made",
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=CLAUDE_CALLBACK,
        )
        RefreshToken.objects.create(user=user, application=connected, token="r")
        for app in (unused, connected, manual):
            self.age(app, 2)

        call_command("clearoauthclients")

        assert set(Application.objects.values_list("pk", flat=True)) == {fresh.pk, connected.pk, manual.pk}

    def test_keeps_a_registration_mid_authorization(self, client, user):
        app = Application.objects.get(client_id=register(client).json()["client_id"])
        Grant.objects.create(
            user=user, application=app, code="c", expires=timezone.now(), redirect_uri=CLAUDE_CALLBACK
        )
        self.age(app, 2)
        call_command("clearoauthclients")
        assert Application.objects.filter(pk=app.pk).exists()
