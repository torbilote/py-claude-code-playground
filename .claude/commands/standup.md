---
description: Quick informal summary of what's in flight across all engagements, for the user's own daily standup
---

> Slash command: a stored prompt template, run in the main conversation (no
> isolation, unlike a subagent). This one takes no arguments — every
> engagement, always — which is why there's no `argument-hint` above and no
> `$ARGUMENTS` below. Compare to `/risk-check` and `/new-engagement`, which
> take one.

Give me a quick standup summary across all my engagements. Run
`py -m delivery_copilot.cli engagement list` to see everything, then for each
engagement that isn't `closed`, briefly note: overall status, anything overdue
or blocking, and what's actively in progress. Keep it to a few lines per
engagement — this is for me to skim before a 9am standup, not a formal report.
End with anything that needs a decision from me today.
