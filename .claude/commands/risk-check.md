---
description: Run a risk sweep via the risk-auditor subagent, optionally scoped to one engagement
argument-hint: [engagement-id]
---

> Slash command with an argument: `argument-hint` above is just UI hinting
> (shown while you type); the actual value comes in wherever `$ARGUMENTS`
> appears below — whatever you typed after `/risk-check`, or an empty string
> if you typed nothing. This command's whole body runs in the main
> conversation; it *delegates* to the `risk-auditor` subagent rather than
> doing the sweep itself.

Use the `risk-auditor` subagent to sweep for stale or high-severity open
risks and overdue tasks, and report the prioritized findings.

Engagement scope: $ARGUMENTS

If an engagement ID was given above, scope the sweep to that engagement
only. If it's empty, sweep every engagement in the portfolio.

Include today's date in the prompt you give the subagent — it has no shell
and no view of this conversation, so it only knows what you tell it, and it
needs the date to judge what's stale or overdue.
