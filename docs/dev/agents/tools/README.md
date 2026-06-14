# Tools

Vendor-neutral specifications for tools / MCP servers and helper scripts the assistants
may use, with enough detail to configure them in any client. When a tool is an MCP server,
the canonical config is mirrored into a root `.mcp.json` (read by MCP-aware clients);
this directory documents *what* the tool is and *why*, independent of any one client.

**Prefer tools implemented as code** (a committed `scripts/` CLI, a function, a Makefile
target) over interactive multi-step agent workflows — it is deterministic, reusable, and
**saves tokens** (see DEVELOPMENT_REQUIREMENTS **D4**). Reach for an MCP server / agentic
tool only when code cannot do the job. Each entry should make outputs compact (filter at
the source; bulky artefacts go to `.tmp/`, report a path).

_None yet._ Add one file per tool, e.g. `<tool-name>.md` (purpose, the command/endpoint to
run, auth/env, inputs/outputs, whether it is code or MCP, client-config snippets).
