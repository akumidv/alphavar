# AI working artifacts (vendor-neutral)

This directory holds the project's **AI-assisted-development artifacts**, kept in-repo so
they are versioned, shared across the team and machines (incl. Windows — no symlinks), and
**LLM-agnostic**: plain Markdown/JSON readable by any assistant (Claude, GPT/Codex,
Gemini, Copilot, …) and by humans. No single vendor's tooling is privileged here.

See [AI_WORKING_MODEL.md](../AI_WORKING_MODEL.md) for the full model and rationale.

Layout:
- [`memory/`](memory/) — durable notes/decisions the assistants should remember. These
  **graduate into formal rules** (`AGENTS.md` / `ARCHITECTURE_REQUIREMENTS.md`) once
  stable.
- [`skills/`](skills/) — reusable task playbooks as plain Markdown (steps, commands,
  checklists). Vendor adapters (e.g. a `.claude/skills/` shim) may reference these, but
  the source of truth lives here.
- [`tools/`](tools/) — tool / MCP server specifications and helper-script docs, vendor-
  neutral. **Prefer tools implemented as code** (scripts/CLI) over interactive agent
  workflows to save tokens (DEVELOPMENT_REQUIREMENTS D4). A root `.mcp.json` (when present)
  is derived from these.
- [`knowledge/`](knowledge/) — concentrated, **sourced** domain knowledge (exchanges &
  their APIs, options, risk, portfolio management, …) so assistants can work without
  re-researching, and re-query the cited source when a note is insufficient.

Canonical **rules** are not here — they live in the vendor-neutral `AGENTS.md` (entry
point) and `docs/dev/ARCHITECTURE_REQUIREMENTS.md` (formal R0…Rn).
