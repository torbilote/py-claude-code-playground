import json

import pytest

from delivery_copilot import store


@pytest.fixture
def temp_store(tmp_path, monkeypatch):
    data_file = tmp_path / "engagements.json"
    data_file.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("DELIVERY_COPILOT_DATA", str(data_file))
    return data_file


def test_add_and_load_engagement(temp_store):
    e = store.add_engagement(client_name="Acme", name="Website Revamp", lead="lead@valtech.com")
    loaded = store.get_engagement(e.id)
    assert loaded is not None
    assert loaded.client_name == "Acme"
    assert loaded.status == "active"


def test_add_risk_and_open_risks(temp_store):
    e = store.add_engagement(client_name="Acme", name="Website Revamp", lead="lead@valtech.com")
    store.add_risk(e.id, description="Vendor delay", severity="high", owner="lead@valtech.com")
    loaded = store.get_engagement(e.id)
    assert len(loaded.open_risks()) == 1
    assert loaded.risks[0].severity == "high"


def test_mitigate_risk(temp_store):
    e = store.add_engagement(client_name="Acme", name="Website Revamp", lead="lead@valtech.com")
    risk = store.add_risk(e.id, description="Vendor delay", severity="high", owner="lead@valtech.com")
    ok = store.mitigate_risk(e.id, risk.id, mitigation="Switched vendors")
    assert ok
    loaded = store.get_engagement(e.id)
    assert loaded.open_risks() == []
    assert loaded.risks[0].status == "mitigated"


def test_log_time_accumulates_hours(temp_store):
    e = store.add_engagement(client_name="Acme", name="Website Revamp", lead="lead@valtech.com")
    store.log_time(e.id, consultant="dev@valtech.com", hours=3)
    store.log_time(e.id, consultant="dev@valtech.com", hours=2.5)
    loaded = store.get_engagement(e.id)
    assert loaded.total_hours() == 5.5


def test_unknown_engagement_returns_none(temp_store):
    assert store.get_engagement("does-not-exist") is None
    assert store.add_risk("does-not-exist", description="x", severity="low", owner="x") is None
