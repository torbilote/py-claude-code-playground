---
name: new-engagement
description: Scaffold a brand-new client engagement end-to-end - collects the essentials, creates the engagement record, and optionally seeds an initial kickoff task and any known day-one risks. Use when the user says they're starting a new client engagement/project or asks to "set up" a new engagement.
argument-hint: [client name]
---

> **Skill, not a script — and also a slash command.** Every skill is
> invocable as `/<name>` (here `/new-engagement`), and it can take arguments
> exactly like a command: `argument-hint` above, `$ARGUMENTS` below. So
> there's no separate `.claude/commands/new-engagement.md` — a command with
> the same name would just collide with this skill. It also still fires on
> its own when your request matches `description`. No bundled script on
> purpose: unlike `status-report`, the work here is a conversation (asking
> clarifying questions), not a data transform.

# New engagement scaffolding

Turns "we just kicked off a new engagement" into a fully recorded
engagement with sensible starting content, using the real `delivery-copilot`
CLI (not by hand-editing `data/engagements.json`).

Client name passed on invocation (empty if none — then ask): $ARGUMENTS

## Steps

1. Ask the user for anything missing, but don't ask for things you can infer
   or default sensibly:
   - Client name (required)
   - Engagement/project name (required)
   - Engagement lead's email (default to the current user's email if this is
     their own engagement and they don't say otherwise)
   - Start date (default: today)
2. Create it:
   ```
   py -m delivery_copilot.cli engagement add --client "<client>" --name "<name>" --lead "<lead>" [--start-date <date>]
   ```
   Capture the printed engagement ID (`eng-xxxxxx`) from the output.
3. Ask if there's a known kickoff task (e.g. "discovery workshop", "SOW
   sign-off") and any day-one risks worth logging (e.g. "client hasn't
   confirmed data access yet"). If yes, add them:
   ```
   py -m delivery_copilot.cli task add <engagement_id> --title "<title>" --assignee "<email>" --due-date <date>
   py -m delivery_copilot.cli risk add <engagement_id> --description "<desc>" --severity <low|medium|high> --owner "<email>"
   ```
   If the user has nothing to add yet, that's fine — don't invent placeholder
   tasks or risks just to have something to show.
4. Finish by running `py -m delivery_copilot.cli engagement show <engagement_id>`
   and showing the user the result so they can confirm it looks right.

## Constraints

- Never fabricate a client name, lead email, or engagement name — always get
  these from the user, even if it means asking a clarifying question first.
- Don't mark the engagement `at-risk` or add risks unless the user actually
  describes a risk; a brand-new engagement defaults to `active`.
