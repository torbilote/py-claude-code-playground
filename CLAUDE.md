# Delivery Copilot

A small toolkit for Valtech consultants to track client engagements: risks,
tasks, and logged time. Built as a hands-on showcase of Claude Code features
(CLAUDE.md, subagents, skills, slash commands, hooks, and an MCP server) —
everything here is real, runnable code, not a toy demo.

## Architecture

- `src/delivery_copilot/` — the library and CLI (`models.py`, `store.py`, `cli.py`).
  `store.py` is the single source of truth for reading/writing engagement data;
  both the CLI and the MCP server go through it. Never read or write
  `data/engagements.json` directly from new code — add a `store.py` function.
- `data/engagements.json` — seed/working data. One JSON array of engagements,
  each with nested `risks`, `tasks`, and `time_entries`. Overridable via the
  `DELIVERY_COPILOT_DATA` env var (tests always set this to a temp file).
- `mcp_server/server.py` — an MCP server: a separate process Claude Code
  talks to over stdio (started automatically per `.mcp.json`) that exposes
  this project's data as three kinds of primitive — **tools** (actions the
  model can call: `list_engagements`, `get_engagement`, `list_open_risks`,
  `add_risk`, `log_time`), **resources** (addressable read-only data you can
  @-mention or the model can fetch: `delivery-copilot://engagements`,
  `delivery-copilot://engagement/{id}`), and **prompts** (reusable templates
  a client can surface, e.g. as a slash command: `portfolio_risk_sweep`).
  This is what makes it "live": editing an engagement through chat and then
  running `delivery-copilot engagement show` (or vice versa) sees the same
  change, because both go through `store.py`. See `mcp_server/CLAUDE.md` for
  the transport-layer conventions.
- `.claude/` — the Claude Code configuration: subagents, skills, slash
  commands, hooks, permissions, and the status line. See below.

## Running things

- Install: `py -m pip install -e ".[dev]"`
- Run the CLI: `py -m delivery_copilot.cli --help` (or the `delivery-copilot` entry point after install)
- Run tests: `py -m pytest -q`
- Run the MCP server standalone (for debugging): `py mcp_server/server.py`

## Conventions

- Python 3.10+, stdlib `dataclasses` for models, no ORM — this is intentionally
  small. Don't add a database or web framework; if the project outgrows JSON,
  raise it with the user first.
- Consultant identity is always an email address (matches how Valtech staff
  are referenced elsewhere). Client names and engagement content are sample
  data — treat anything under `data/` as if it were real client data for
  handling purposes (see confidentiality rule below), even though it's fictional.
- Keep CLI output ASCII-only. This project is developed and demoed on Windows
  terminals with non-UTF8 codepages (cp1250/cp1252); em dashes, curly quotes,
  and emoji in `click.echo()` output have caused `UnicodeEncodeError` before.
  Stick to `-` instead of `—` and plain text instead of symbols/emoji in
  anything printed to stdout.

## Confidentiality

Engagement data (client names, risks, financials, timesheets) is treated as
client-confidential, per Valtech policy, even in this sample project. Don't
paste engagement contents into commit messages, external issues, or anywhere
outside this repo. The `secret-scanner` subagent and the `block_secrets` hook
exist to catch *credentials* specifically (API keys, tokens, connection
strings) — they are not a substitute for using judgment about client data.

## Subagents, skills, and commands available here

Three mechanisms that are easy to conflate — the distinction is what each
one *has access to*:

- A **subagent** (`.claude/agents/*.md`) runs in its own isolated context
  window. It never sees this conversation's history, can only use the tools
  listed in its `tools:` frontmatter, and hands back one final report — good
  for focused, tool-restricted work like a read-only audit.
- A **skill** (`.claude/skills/*/SKILL.md`) is instructions (plus optional
  bundled scripts) pulled *into* the current conversation when its
  `description` matches what you're asking for. No isolation, no tool
  restriction — it's know-how, not a separate agent.
- A **slash command** (`.claude/commands/*.md`) is a single-file prompt
  template, invoked by typing `/<name>`. Whatever you type after the name
  becomes `$ARGUMENTS`. Commands and skills have converged: every skill is
  also invocable as `/<name>` and can take `$ARGUMENTS`, and commands show
  up in the model's skill list too. The practical difference is shape — a
  command is one file, a skill is a folder that can bundle scripts. That's
  why `new-engagement` exists only as a skill here: a command with the same
  name would collide with it.

- **Subagent `risk-auditor`** — reviews engagement data for stale/high-severity
  open risks and overdue tasks; produces a prioritized findings list. Good for
  "sweep all engagements before Monday's leadership sync." Read-only by
  construction (only read-only MCP tools, no Bash) and runs on `haiku`.
- **Subagent `secret-scanner`** — scans the working tree / staged diff for
  leaked credentials before a commit. Complements the `block_secrets` hook
  (the hook is a fast hard block; the subagent gives reasoned, broader review).
- **Skill `status-report`** — turns one engagement's data into a polished,
  client-ready Markdown status report.
- **Skill `new-engagement`** (`/new-engagement [client name]`) — scaffolds a
  new engagement record end-to-end (asks clarifying questions, then calls the
  CLI to create it).
- **Command `/standup`** — quick informal summary of what's in flight across
  all engagements, for the consultant's own daily standup.
- **Command `/risk-check [engagement-id]`** — invokes the `risk-auditor`
  subagent, optionally scoped to one engagement via `$ARGUMENTS`.

## Hooks

Hooks are shell commands the Claude Code *harness* runs automatically around
specific events — they execute outside the model's control, so they're the
right place for a hard guarantee (a block that can't be reasoned around),
not just an instruction the model might skip. Each hook gets a JSON payload
on stdin (event name, tool name, tool input, etc.) and answers back via exit
code: `0` = success/continue, `2` = blocking error (on `PreToolUse` the tool
call is blocked and the hook's stderr is fed to the model as the reason),
any other non-zero = non-blocking error (shown to you, the call proceeds).
That last case matters: a hook that crashes does *not* block, so a security
hook must fail with exit 2 on purpose. The `matcher` field is a regex against
the tool name (omitted for non-tool events like `SessionStart`). Hook
commands use `"$CLAUDE_PROJECT_DIR/..."` rather than relative paths, because
the working directory can change mid-session (e.g. after a `cd`).

Configured in `.claude/settings.json`:

- `SessionStart` — runs `.claude/hooks/session_risk_glance.py`, which prints a
  one-line heads-up on high-severity open risks / overdue tasks when a
  session opens in this project. Silent if there's nothing urgent.
- `PreToolUse` on `Bash|Write|Edit` — runs `.claude/hooks/block_secrets.py`,
  which blocks any tool call whose input matches common credential patterns
  (AWS keys, private key headers, bearer tokens, etc.) before it executes.
  This is live, not simulated — it will block Claude's own tool calls in this
  session, same as it did while this project was being built.
- `PostToolUse` on `Bash|Write|Edit` — runs `.claude/hooks/audit_log.py`,
  appending a one-line record of every file/command mutation to
  `.claude/audit.log` (gitignored) — a lightweight audit trail, in the spirit
  of Valtech's least-privilege/auditability guidance for admin-adjacent tooling.

## Permissions and status line

- `.claude/settings.json` also carries a `permissions` block: a declarative
  allow/ask/deny list for tool calls — pure pattern matching, no code (hooks
  are the code-based counterpart). Rules look like `Bash(py -m pytest:*)`
  (prefix match, `:*` = "and anything after"), `Read(./data/**)` (glob on
  file tools), or `mcp__delivery-copilot__list_engagements` (MCP tools are
  named `mcp__<server>__<tool>`). Here: tests, the CLI, and the three
  *read-only* MCP tools are pre-allowed; the MCP tools that write
  (`add_risk`, `log_time`) still prompt; `git push` always asks; `rm -rf` and
  force-push are denied outright. Different trust levels for different risk
  levels.
- `enabledMcpjsonServers` pre-approves the `.mcp.json` server. Without it,
  Claude Code asks whether to trust a project-defined MCP server the first
  time — a deliberate safety gate, since `.mcp.json` launches a local process.
- `statusLine` runs a command on every render and prints its stdout as the
  status bar text; the command receives session context (model name, cwd,
  cost so far) as JSON on stdin. Ours, `.claude/statusline.py`, uses the
  model name from that payload plus live portfolio risk counts read straight
  from `data/engagements.json` — proof a status line isn't just cosmetic, it
  can reflect real project state.
