"""JSON-backed storage for engagements.

Both the CLI (delivery_copilot.cli) and the MCP server (mcp_server.server)
read and write through this module, so they always see the same data.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import date
from pathlib import Path

from delivery_copilot.models import Engagement, Risk, Task, TimeEntry

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "engagements.json"


def _data_path() -> Path:
    override = os.environ.get("DELIVERY_COPILOT_DATA")
    return Path(override) if override else DEFAULT_DATA_PATH


def load_engagements() -> list[Engagement]:
    path = _data_path()
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Engagement.from_dict(e) for e in raw]


def save_engagements(engagements: list[Engagement]) -> None:
    path = _data_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [e.to_dict() for e in engagements]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_engagement(engagement_id: str) -> Engagement | None:
    for e in load_engagements():
        if e.id == engagement_id:
            return e
    return None


def _short_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6]}"


def add_engagement(client_name: str, name: str, lead: str, start_date: str | None = None) -> Engagement:
    engagements = load_engagements()
    engagement = Engagement(
        id=_short_id("eng"),
        client_name=client_name,
        name=name,
        lead=lead,
        start_date=start_date or date.today().isoformat(),
    )
    engagements.append(engagement)
    save_engagements(engagements)
    return engagement


def add_risk(engagement_id: str, description: str, severity: str, owner: str) -> Risk | None:
    engagements = load_engagements()
    for e in engagements:
        if e.id == engagement_id:
            risk = Risk(
                id=_short_id("risk"),
                description=description,
                severity=severity,
                owner=owner,
                opened_date=date.today().isoformat(),
            )
            e.risks.append(risk)
            save_engagements(engagements)
            return risk
    return None


def mitigate_risk(engagement_id: str, risk_id: str, mitigation: str) -> bool:
    engagements = load_engagements()
    for e in engagements:
        if e.id != engagement_id:
            continue
        for r in e.risks:
            if r.id == risk_id:
                r.status = "mitigated"
                r.mitigation = mitigation
                save_engagements(engagements)
                return True
    return False


def add_task(engagement_id: str, title: str, assignee: str, due_date: str) -> Task | None:
    engagements = load_engagements()
    for e in engagements:
        if e.id == engagement_id:
            task = Task(id=_short_id("task"), title=title, assignee=assignee, due_date=due_date)
            e.tasks.append(task)
            save_engagements(engagements)
            return task
    return None


def log_time(engagement_id: str, consultant: str, hours: float, note: str = "", task_id: str | None = None) -> TimeEntry | None:
    engagements = load_engagements()
    for e in engagements:
        if e.id == engagement_id:
            entry = TimeEntry(
                date=date.today().isoformat(),
                consultant=consultant,
                hours=hours,
                note=note,
                task_id=task_id,
            )
            e.time_entries.append(entry)
            save_engagements(engagements)
            return entry
    return None
