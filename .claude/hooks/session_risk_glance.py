#!/usr/bin/env python3
"""SessionStart hook: surface urgent portfolio risk the moment a session opens.

Unlike PreToolUse/PostToolUse (which key off a `matcher` on tool name),
SessionStart isn't about tool calls at all - it fires once per session start
(fresh, resumed, or after /clear; the payload's `source` field says which,
if you need to distinguish). Whatever this script prints to stdout on exit 0
gets folded into the model's context for that session, same mechanism
`UserPromptSubmit` hooks use to inject context on every turn - here it's just
once, at the start. Stays silent if there's nothing urgent: this is meant to
save a delivery lead from re-checking the portfolio every morning, not to
nag on every launch.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from delivery_copilot import store  # noqa: E402


def main() -> int:
    try:
        engagements = store.load_engagements()
    except Exception:
        return 0

    today = date.today()
    high_risks = []
    overdue_tasks = []

    for e in engagements:
        for r in e.open_risks():
            if r.severity == "high":
                high_risks.append(f"{e.client_name}: {r.description}")
        for t in e.tasks:
            if t.status == "done":
                continue
            try:
                if date.fromisoformat(t.due_date) < today:
                    overdue_tasks.append(f"{e.client_name}: {t.title} (was due {t.due_date})")
            except ValueError:
                continue

    if not high_risks and not overdue_tasks:
        return 0

    lines = ["[delivery-copilot heads-up]"]
    if high_risks:
        lines.append(f"- {len(high_risks)} high-severity open risk(s): " + "; ".join(high_risks))
    if overdue_tasks:
        lines.append(f"- {len(overdue_tasks)} overdue task(s): " + "; ".join(overdue_tasks))
    lines.append("Run /risk-check for the full prioritized sweep.")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
