"""MCP server exposing live engagement data to Claude Code.

Backed by the same JSON store the `delivery-copilot` CLI uses, so anything
logged through chat (via these tools) is immediately visible to the CLI,
and vice versa. Run standalone with:

    py mcp_server/server.py

Registered for Claude Code via .mcp.json at the repo root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make the local `delivery_copilot` package importable without requiring
# an editable install — keeps the showcase runnable with zero setup.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp.server.fastmcp import FastMCP

from delivery_copilot import store

mcp = FastMCP("delivery-copilot")


@mcp.tool()
def list_engagements() -> list[dict]:
    """List all client engagements with their status and open risk count."""
    return [
        {
            "id": e.id,
            "client_name": e.client_name,
            "name": e.name,
            "status": e.status,
            "lead": e.lead,
            "open_risk_count": len(e.open_risks()),
        }
        for e in store.load_engagements()
    ]


@mcp.tool()
def get_engagement(engagement_id: str) -> dict:
    """Get full detail for one engagement: risks, tasks, and time entries."""
    e = store.get_engagement(engagement_id)
    if not e:
        return {"error": f"no engagement found with id '{engagement_id}'"}
    return e.to_dict()


@mcp.tool()
def list_open_risks(engagement_id: str | None = None) -> list[dict]:
    """List open risks, optionally filtered to a single engagement.

    Useful for a portfolio-wide risk sweep across all active client work.
    """
    engagements = store.load_engagements()
    if engagement_id:
        engagements = [e for e in engagements if e.id == engagement_id]
    results = []
    for e in engagements:
        for r in e.open_risks():
            results.append({"engagement_id": e.id, "client_name": e.client_name, **r.to_dict()})
    return results


@mcp.tool()
def add_risk(engagement_id: str, description: str, severity: str, owner: str) -> dict:
    """Log a new risk against an engagement. severity must be low, medium, or high."""
    if severity not in ("low", "medium", "high"):
        return {"error": "severity must be one of: low, medium, high"}
    risk = store.add_risk(engagement_id, description=description, severity=severity, owner=owner)
    if not risk:
        return {"error": f"no engagement found with id '{engagement_id}'"}
    return risk.to_dict()


@mcp.tool()
def log_time(engagement_id: str, consultant: str, hours: float, note: str = "", task_id: str | None = None) -> dict:
    """Log billable hours for a consultant against an engagement."""
    entry = store.log_time(engagement_id, consultant=consultant, hours=hours, note=note, task_id=task_id)
    if not entry:
        return {"error": f"no engagement found with id '{engagement_id}'"}
    return entry.to_dict()


# --- Resources: addressable data, distinct from tools (no arguments to fill
# in, just a URI a client can read or a user can @-mention). ---


@mcp.resource("delivery-copilot://engagements")
def engagements_index() -> str:
    """Index of all engagement IDs, clients, and statuses, as JSON."""
    return json.dumps(
        [
            {"id": e.id, "client_name": e.client_name, "name": e.name, "status": e.status}
            for e in store.load_engagements()
        ],
        indent=2,
    )


@mcp.resource("delivery-copilot://engagement/{engagement_id}")
def engagement_resource(engagement_id: str) -> str:
    """Full raw JSON record for one engagement, addressable by ID."""
    e = store.get_engagement(engagement_id)
    if not e:
        return json.dumps({"error": f"no engagement found with id '{engagement_id}'"})
    return json.dumps(e.to_dict(), indent=2)


# --- Prompts: reusable prompt templates a client can surface (in Claude
# Code these show up as /mcp__delivery-copilot__<name> slash commands). ---


@mcp.prompt(title="Portfolio risk sweep")
def portfolio_risk_sweep() -> str:
    """Ask for a prioritized risk/overdue-task sweep across every engagement."""
    return (
        "Review every engagement via the delivery-copilot MCP tools and flag: "
        "open high-severity risks, risks open longer than 14 days, and overdue "
        "tasks. Prioritize the list, most urgent first, grouped by client."
    )


if __name__ == "__main__":
    mcp.run()
