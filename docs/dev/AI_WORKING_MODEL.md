# AI working model — where AI-development artifacts live

How this repository organizes artifacts for **AI-assisted development**. The product is
not an AI system; it is built *with* AI assistants, by a **team**, on **mixed OSes
(incl. Windows)**, using **several different LLMs/tools** (Claude, GPT/Codex, Gemini,
Copilot, …). Therefore every artifact is **committed to the repo**, **vendor-neutral**
(plain Markdown/JSON, no tool privileged), and **symlink-free** (Windows-safe).

## Model (decided 2026-06-14)

```
repo/
  AGENTS.md                         # CANONICAL agent rules — the single entry point (all LLMs)
  CLAUDE.md                         # thin pointer → AGENTS.md
  .github/copilot-instructions.md   # thin pointer → AGENTS.md
  <GEMINI.md | .cursor/rules | …>   # add a thin pointer per tool a teammate uses
  .mcp.json                         # optional: MCP tools, mirrored from docs/dev/agents/tools/
  docs/dev/
    ARCHITECTURE_REQUIREMENTS.md    # architecture/domain rules R0…R8 (new entities / domain changes)
    DEVELOPMENT_REQUIREMENTS.md     # day-to-day dev rules D1…D3 (every change)
    AI_WORKING_MODEL.md             # this file
    agents/                         # vendor-neutral AI artifacts (Markdown/JSON)
      README.md
      memory/                       # durable notes/decisions → graduate into rules
      skills/                       # task playbooks (plain Markdown)
      tools/                        # tool / MCP specs (prefer code; vendor-neutral)
      knowledge/                    # concentrated, sourced domain knowledge
```

### Rules

- **Canonical, vendor-neutral.** `AGENTS.md` is the one entry point (an emerging
  cross-tool standard); formal rules live in `docs/dev/ARCHITECTURE_REQUIREMENTS.md`
  (architecture/domain, R0…R8) and `docs/dev/DEVELOPMENT_REQUIREMENTS.md` (day-to-day, D1…D3).
- **Per-tool files are thin pointers**, never a second source of truth: `CLAUDE.md`,
  `.github/copilot-instructions.md`, etc. each just say "see AGENTS.md". Add one when a
  teammate adopts a new tool; deleting it loses nothing.

### Memory, skills, tools

- Live under `docs/dev/agents/` as plain Markdown/JSON so **any** assistant or human can
  read them — not under a Claude-only (`.claude/`) or other vendor directory.
- **Memory** = durable notes the assistants should carry between sessions. Stable items
  **graduate** into `AGENTS.md` / `ARCHITECTURE_REQUIREMENTS.md` /
  `DEVELOPMENT_REQUIREMENTS.md`, leaving a back-link.
- **Skills** = reusable task playbooks (steps + exact commands + verify checklist).
- **Tools** = tool/MCP specs; **prefer tools implemented as code** (scripts/CLI) over
  interactive agent workflows to cut token usage and gain determinism
  (DEVELOPMENT_REQUIREMENTS D4). MCP-aware clients also read a generated root `.mcp.json`.
- **Knowledge** = concentrated, **sourced** domain reference (exchanges/APIs, options,
  risk, portfolio, …) so assistants don't re-research from scratch and can re-query the
  cited source on demand. Distinct from memory (project ways-of-working) and rules.
- If a specific client needs auto-discovery (e.g. Claude Code's `.claude/skills/`), add a
  **thin adapter** that *references* the neutral file — never the canonical copy, and
  never a symlink.

## Options considered

1. **AGENTS.md-canonical + neutral `docs/dev/agents/` (chosen).** Rules neutral in
   AGENTS.md/docs; memory/skills/tools neutral Markdown; per-tool pointer files; optional
   thin vendor adapters. Multi-LLM, team- and Windows-friendly, no glue beyond pointers.
2. **Neutral top-level `ai/` umbrella with a sync step.** Single source `ai/{rules,memory,
   skills,tools}` plus a script that regenerates vendor dirs. Most tool-agnostic but adds
   a build/sync step to keep copies in lockstep — rejected as premature.
3. **Everything under `.claude/`.** Simplest, one place — rejected: Claude-only, unreadable
   by the other LLMs/tools the team uses, and `AGENTS.md`-ecosystem tools ignore it.

## Status

WIP — `skills/` and `tools/` are scaffolding (README only). The model itself is the
decision to record; populate as concrete skills/tools emerge.
