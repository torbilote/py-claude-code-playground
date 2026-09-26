# MCP server conventions (directory-scoped)

Claude Code loads this file in addition to the root `CLAUDE.md` whenever
work touches this directory specifically — that's the whole point of
directory-scoped `CLAUDE.md` files: keep transport-layer concerns here
instead of bloating the root file with details that only matter here.

- A `@mcp.tool()` function's docstring becomes the tool description shown to
  the model when deciding whether to call it — keep it one clear sentence,
  written for that decision, not as human API docs.
- All three MCP primitives are used here on purpose, as a learning surface:
  `@mcp.tool()` for actions, `@mcp.resource()` for addressable read-only data
  (`delivery-copilot://engagements`, `delivery-copilot://engagement/{id}`),
  and `@mcp.prompt()` for a reusable prompt template. Keep that shape when
  adding new capabilities — don't turn a resource into a tool just to avoid
  learning the resource decorator.
- Everything here goes through `delivery_copilot.store`, same rule as the
  CLI — never touch `data/engagements.json` directly.
- After changing a tool/resource/prompt signature, reconnect the MCP server
  in Claude Code (`/mcp`) — a running connection doesn't hot-reload.
