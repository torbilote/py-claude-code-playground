import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "block_secrets.py"

# Fake secrets are assembled at runtime: written out literally, they would be
# blocked by the very hook under test when this file is edited via Claude Code.
FAKE_AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"
FAKE_PRIVATE_KEY = "-----BEGIN RSA " + "PRIVATE KEY-----"
FAKE_CONN_STRING = "postgres://admin:" + "hunter2@db.internal/app"


def run_hook(tool_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)


def test_allows_benign_command():
    assert run_hook("Bash", {"command": "py -m pytest -q"}).returncode == 0


@pytest.mark.parametrize(
    "tool_name,tool_input",
    [
        ("Bash", {"command": f"export AWS_KEY={FAKE_AWS_KEY}"}),
        ("Write", {"file_path": "key.pem", "content": FAKE_PRIVATE_KEY}),
        ("Edit", {"file_path": "cfg.py", "old_string": "x", "new_string": f"DB = '{FAKE_CONN_STRING}'"}),
    ],
)
def test_blocks_secrets_with_exit_code_2(tool_name, tool_input):
    result = run_hook(tool_name, tool_input)
    assert result.returncode == 2
    assert "Blocked" in result.stderr


def test_blocked_message_masks_the_secret():
    result = run_hook("Bash", {"command": f"echo {FAKE_AWS_KEY}"})
    assert FAKE_AWS_KEY not in result.stderr
