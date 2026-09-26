#!/usr/bin/env python3
"""PreToolUse hook: block Bash/Write/Edit calls that contain likely credentials.

Reads the tool-call payload Claude Code sends on stdin (JSON with at least
`tool_name` and `tool_input`), flattens every string value in `tool_input`,
and checks it against a list of common secret patterns. On a match, prints a
short explanation to stderr and exits 2, which Claude Code treats as "block
this tool call and show Claude the stderr text" so it can course-correct
(e.g. suggest an env var instead) rather than just failing silently.

This is a fast, deterministic backstop for the org rule "never ask for or
expose passwords, API keys, tokens, private keys, cookies, or connection
strings" - it complements (does not replace) the `secret-scanner` subagent,
which does a slower, reasoned sweep.
"""

from __future__ import annotations

import json
import re
import sys

PATTERNS = [
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Private key header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("Generic API key/secret assignment", re.compile(
        r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][A-Za-z0-9/+._-]{8,}['\"]"
    )),
    ("Bearer token", re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}")),
    ("Connection string with embedded credentials", re.compile(
        r"[a-zA-Z]+://[^\s:/'\"]+:[^\s@/'\"]+@"
    )),
]


def flatten_strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out = []
        for v in value.values():
            out.extend(flatten_strings(v))
        return out
    if isinstance(value, list):
        out = []
        for v in value:
            out.extend(flatten_strings(v))
        return out
    return []


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_input = payload.get("tool_input", {})
    haystack = "\n".join(flatten_strings(tool_input))

    hits = []
    for label, pattern in PATTERNS:
        m = pattern.search(haystack)
        if m:
            snippet = m.group(0)
            masked = snippet[:4] + "..." + snippet[-4:] if len(snippet) > 10 else "***"
            hits.append(f"{label} (matched: {masked})")

    if hits:
        print(
            "Blocked: this tool call looks like it contains a credential:\n- "
            + "\n- ".join(hits)
            + "\n\nRemove the secret and use an environment variable or a secrets "
            "manager reference instead. If this is a false positive (e.g. an "
            "obviously fake test fixture), say so and rephrase so it doesn't "
            "match a real key format.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
