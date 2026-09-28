import asyncio
import json
import os
from unittest.mock import patch

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

import db
from db import ApplicationStatus
from server import _build_transport_security, BearerAuthMiddleware, get_pipeline, mcp


def test_get_pipeline_filters_by_offer_received(isolated_db):
    offer_id = db.add_application("Offer Corp", "Engineer")
    db.update_status(offer_id, ApplicationStatus.OFFER)
    db.add_application("Other Corp", "Engineer")

    result = get_pipeline(ApplicationStatus.OFFER)
    assert "Offer Corp" in result
    assert "Other Corp" not in result


def test_get_pipeline_without_filter_lists_all(isolated_db):
    db.add_application("A Corp", "Engineer")
    db.add_application("B Corp", "Engineer")

    result = get_pipeline()
    assert "A Corp" in result and "B Corp" in result


def test_get_pipeline_schema_exposes_valid_statuses():
    """Clients should see the real enum values, so 'Offer' can't be guessed."""
    tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
    schema = json.dumps(tools["get_pipeline"].inputSchema)
    for status in ApplicationStatus:
        assert status.value in schema


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


def test_bearer_auth_rejects_non_ascii_token():
    client = _make_test_app()
    resp = client.get("/", headers={"Authorization": "Bearer sécret".encode("latin-1")})
    assert resp.status_code == 401


def test_bearer_auth_accepts_correct_token():
    client = _make_test_app()
    resp = client.get("/", headers={"Authorization": "Bearer secret"})
    assert resp.status_code == 200