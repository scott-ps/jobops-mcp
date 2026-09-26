import os
from unittest.mock import patch

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from server import _build_transport_security, BearerAuthMiddleware


def test_transport_security_none_when_unset():
    with patch.dict(os.environ, {}, clear=True):
        assert _build_transport_security() is None


def test_transport_security_allowlists_host_when_set():
    with patch.dict(os.environ, {"MCP_ALLOWED_HOST": "example.com"}):
        settings = _build_transport_security()
        assert "example.com" in settings.allowed_hosts
        assert "https://example.com" in settings.allowed_origins


def _make_test_app(token="secret"):
    app = Starlette(routes=[Route("/", lambda r: PlainTextResponse("ok"))])
    app.add_middleware(BearerAuthMiddleware, token=token)
    return TestClient(app)


def test_bearer_auth_rejects_missing_header():
    client = _make_test_app()
    assert client.get("/").status_code == 401


def test_bearer_auth_rejects_wrong_token():
    client = _make_test_app()
    resp = client.get("/", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401


def test_bearer_auth_accepts_correct_token():
    client = _make_test_app()
    resp = client.get("/", headers={"Authorization": "Bearer secret"})
    assert resp.status_code == 200