import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mcp_server"))

import server  # noqa: E402

from delivery_copilot import store  # noqa: E402


@pytest.fixture
def engagement(tmp_path, monkeypatch):
    data_file = tmp_path / "engagements.json"
    data_file.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("DELIVERY_COPILOT_DATA", str(data_file))
    return store.add_engagement(client_name="Acme", name="Revamp", lead="lead@example.com")


def test_registers_all_three_mcp_primitives():
    tools = {t.name for t in asyncio.run(server.mcp.list_tools())}
    templates = {str(t.uriTemplate) for t in asyncio.run(server.mcp.list_resource_templates())}
    resources = {str(r.uri) for r in asyncio.run(server.mcp.list_resources())}
    prompts = {p.name for p in asyncio.run(server.mcp.list_prompts())}

    assert tools == {"list_engagements", "get_engagement", "list_open_risks", "add_risk", "log_time"}
    assert "delivery-copilot://engagement/{engagement_id}" in templates
    assert "delivery-copilot://engagements" in resources
    assert prompts == {"portfolio_risk_sweep"}


def test_add_risk_via_mcp_is_visible_to_store(engagement):
    server.add_risk(engagement.id, description="Vendor delay", severity="high", owner="lead@example.com")
    assert len(store.get_engagement(engagement.id).open_risks()) == 1


def test_add_risk_rejects_invalid_severity(engagement):
    assert "error" in server.add_risk(engagement.id, description="x", severity="urgent", owner="a@example.com")


def test_engagement_resource_returns_json(engagement):
    data = json.loads(server.engagement_resource(engagement.id))
    assert data["client_name"] == "Acme"
