#!/usr/bin/env python3
"""Custom status line: model name plus live portfolio risk state.

Claude Code invokes this on every render, piping session context as JSON on
stdin (model name, workspace, cost, etc — see the statusLine docs). We only
use the model name from that payload; the risk numbers come straight from
the same data store the CLI and MCP server use, so the status line reflects
edits made through any of them in real time.

Keep this fast (it runs constantly) and ASCII-only (see root CLAUDE.md).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from delivery_copilot import store  # noqa: E402


def main() -> int:
    try:
        ctx = json.load(sys.stdin)
    except Exception:
        ctx = {}
    model_name = ctx.get("model", {}).get("display_name", "Claude")

    try:
        engagements = store.load_engagements()
    except Exception:
        engagements = []

    at_risk = sum(1 for e in engagements if e.status == "at-risk")
    open_total = sum(len(e.open_risks()) for e in engagements)
    high_total = sum(1 for e in engagements for r in e.open_risks() if r.severity == "high")

    parts = [model_name, "delivery-copilot"]
    if engagements:
        parts.append(f"{at_risk}/{len(engagements)} engagements at-risk")
        parts.append(f"{open_total} open risks ({high_total} high)")

    print(" | ".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
