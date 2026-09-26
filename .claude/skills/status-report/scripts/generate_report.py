"""Print structured Markdown status-report data for one engagement.

Usage: py .claude/skills/status-report/scripts/generate_report.py <engagement_id>

Kept deliberately mechanical (no prose/judgment) so its output is a reliable
factual base for the assistant to polish, per the status-report skill.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from delivery_copilot import store  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: generate_report.py <engagement_id>", file=sys.stderr)
        return 2

    engagement_id = sys.argv[1]
    e = store.get_engagement(engagement_id)
    if not e:
        print(f"error: no engagement found with id '{engagement_id}'", file=sys.stderr)
        return 1

    today = date.today()
    week_out = today + timedelta(days=7)

    print(f"# Status Report - {e.client_name}: {e.name}")
    print()
    print(f"- Engagement ID: {e.id}")
    print(f"- Overall status: {e.status}")
    print(f"- Lead: {e.lead}")
    print(f"- Hours logged to date: {e.total_hours()}")
    print()

    open_risks = sorted(e.open_risks(), key=lambda r: {"high": 0, "medium": 1, "low": 2}[r.severity])
    print(f"## Risks ({len(open_risks)} open)")
    if not open_risks:
        print("- None currently open.")
    for r in open_risks:
        print(f"- [{r.severity}] {r.description} (owner: {r.owner}, opened {r.opened_date})")
    print()

    overdue = [t for t in e.tasks if t.status != "done" and date.fromisoformat(t.due_date) < today]
    due_soon = [
        t
        for t in e.tasks
        if t.status != "done" and today <= date.fromisoformat(t.due_date) <= week_out
    ]
    other_open = [t for t in e.tasks if t.status != "done" and t not in overdue and t not in due_soon]

    print(f"## Overdue tasks ({len(overdue)})")
    if not overdue:
        print("- None.")
    for t in overdue:
        print(f"- {t.title} (was due {t.due_date}, assignee: {t.assignee}, status: {t.status})")
    print()

    print(f"## Due within 7 days ({len(due_soon)})")
    if not due_soon:
        print("- None.")
    for t in due_soon:
        print(f"- {t.title} (due {t.due_date}, assignee: {t.assignee}, status: {t.status})")
    print()

    print(f"## Other open tasks ({len(other_open)})")
    if not other_open:
        print("- None.")
    for t in other_open:
        print(f"- {t.title} (due {t.due_date}, assignee: {t.assignee}, status: {t.status})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
