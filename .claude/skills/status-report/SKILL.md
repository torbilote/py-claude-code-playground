---
name: status-report
description: Generate a polished, client-ready Markdown status report for one engagement — pulls live data (risks, tasks, hours) via the bundled script rather than summarizing from memory. Use whenever the user asks for a status report, client update, or weekly/QBR summary for a specific engagement.
---

> **Skill, not a subagent.** Claude Code loads these instructions straight
> into *this* conversation when `description` above matches what you asked
> for — there's no dedicated slash command for this one, description
> matching alone is enough. No isolated context, no restricted tools. A
> skill folder can bundle scripts alongside its `SKILL.md`; this one uses
> `scripts/generate_report.py` as a deterministic data step so the model
> polishes real numbers instead of inventing them.

# Status report generation

Produces a client-facing status report from live engagement data. Always
compute from real data via the script below — never hallucinate hours,
risk counts, or task status from a prior conversation.

## Steps

1. If the user didn't specify which engagement, run
   `py -m delivery_copilot.cli engagement list` (or the `list_engagements`
   MCP tool if available) and ask them to pick one.
2. Run the bundled script to get structured data:
   ```
   py .claude/skills/status-report/scripts/generate_report.py <engagement_id>
   ```
   This prints Markdown built directly from `data/engagements.json` (hours
   totals, open risks by severity, tasks due this/next week, overdue tasks).
3. Take that Markdown as your factual base and turn it into a genuinely
   client-ready report:
   - Write a 2-3 sentence executive summary at the top in plain business
     language (no internal jargon like task IDs).
   - Keep the risk and task sections from the script mostly as-is — they're
     already accurate — but tighten the wording for an external audience.
     Don't invent mitigations that aren't in the data; if a risk has no
     mitigation on file, say "mitigation plan in progress" rather than
     inventing one.
   - Do not include internal-only fields: consultant emails in the time log,
     internal task IDs, or the raw engagement ID. Use names/roles instead
     where the data allows, and omit IDs entirely from client-facing output.
4. Present the final Markdown to the user. Ask whether they want it saved to
   a file (e.g. `reports/<engagement_id>-status-<date>.md`) before writing
   anything — don't create the file unprompted.

## Confidentiality note

This report may contain real client risk/financial context. Treat the
output like any other client deliverable per Valtech policy — the user
decides where it goes (email, deck, portal), not this skill.
