#!/usr/bin/env python3
"""PostToolUse hook: append a one-line audit record for every mutating tool call.

Runs *after* the matched tool call already succeeded (see `block_secrets.py`
for the PreToolUse/blocking counterpart) - so unlike that hook, nothing here
can prevent anything; the only lever a PostToolUse hook has is its exit code
controlling whether its stdout/stderr is shown back to the model, which we
don't need since this is a side-effect-only logger. Claude Code passes the
same kind of payload to every hook: JSON on stdin with at least `tool_name`
and `tool_input` (shape varies per tool - a Bash call has `command`, an Edit
has `file_path`/`old_string`/`new_string`, etc).

Least-privilege tooling should be auditable - this gives a plain-text trail
of every Bash/Write/Edit call Claude made in this project, without needing
any external logging setup. Local-only, gitignored; not a substitute for
real audit logging on anything that touches production systems.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[1] / "audit.log"


def summarize(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        cmd = str(tool_input.get("command", "")).replace("\n", " ")
        return cmd[:200]
    if tool_name in ("Write", "Edit", "NotebookEdit"):
        return str(tool_input.get("file_path", tool_input.get("notebook_path", "?")))
    return json.dumps(tool_input)[:200]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_name = payload.get("tool_name", "unknown")
    tool_input = payload.get("tool_input", {})
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    line = f"{timestamp}  {tool_name}  {summarize(tool_name, tool_input)}\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
