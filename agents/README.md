# AI working model — `agents/`

This directory holds the project's **AI-assisted-development artifacts**, kept in-repo so
they are versioned, shared across the team and machines (incl. Windows — no symlinks), and
**LLM-agnostic**: plain Markdown/JSON readable by any assistant (Claude, GPT/Codex,
Gemini, Copilot, …) and by humans. The product is not an AI system; it is *built with* AI
assistants. No single vendor's tooling is privileged here.

Canonical **rules** are not here — they live in the vendor-neutral root `AGENTS.md` (entry
point) and `docs/dev/{ARCHITECTURE_REQUIREMENTS,DEVELOPMENT_REQUIREMENTS}.md` (R#/D#).

## Layout

```
repo/
  AGENTS.md                         # CANONICAL agent rules — single entry point (all LLMs)
  CLAUDE.md / .github/copilot-instructions.md / …   # thin pointers → AGENTS.md
  .mcp.json                         # optional: MCP tools, mirrored from agents/tools/
  agents/                           # ← THIS DIR (repo root, NOT docs/ — see "Why root")
    README.md                       # this file (the working model + rationale)
    memory/                         # durable notes/decisions → graduate into rules
    skills/                         # task playbooks (plain Markdown: steps, commands, verify)
    tools/                          # tools = code; docs in the package docstring
      <tool_pkg>/                   # the code (CLI/functions), reused not regenerated;
                                    #   purpose + run command live in its __main__ docstring
      <tool>.md                     # ONLY for MCP/external tools (config not in the code)
    knowledge/                      # concentrated, sourced domain knowledge
  docs/dev/
    ARCHITECTURE_REQUIREMENTS.md    # architecture/domain rules R0…R8
    DEVELOPMENT_REQUIREMENTS.md     # day-to-day dev rules D1…D4
    PROJECT_OVERVIEW.md             # design overview
```

- [`memory/`](memory/) — durable notes the assistants should carry between sessions.
  Stable items **graduate** into `AGENTS.md` / `ARCHITECTURE_REQUIREMENTS.md` /
  `DEVELOPMENT_REQUIREMENTS.md`, leaving a back-link. **Read at session start.**
- [`skills/`](skills/) — reusable task playbooks (goal, preconditions, ordered steps,
  exact commands, verify checklist). A skill may reference a tool here rather than inline
  its code. Vendor adapters (e.g. a `.claude/skills/` shim) reference these, never copy.
- [`tools/`](tools/) — tool/MCP specs **and the executable code next to the spec**
  (e.g. `tools/exchange_fixtures/`). **Prefer tools implemented as code** (CLI/functions)
  over interactive agent workflows — deterministic, reusable, token-saving (D4). A root
  `.mcp.json`, when present, is derived from these.
- [`knowledge/`](knowledge/) — concentrated, **sourced** domain reference (exchanges &
  their APIs, options, risk, portfolio) so assistants work without re-researching and can
  re-query the cited source. **Consult before re-researching the domain.**

## Per-tool rule files are thin pointers

`AGENTS.md` (repo root) is the one entry point — an emerging cross-tool standard read
natively by Claude Code, Codex, Cursor, Copilot, Gemini, etc. Per-tool files (`CLAUDE.md`,
`.github/copilot-instructions.md`, …) each just say "see AGENTS.md"; add one when a
teammate adopts a tool, deleting it loses nothing. Never a second source of truth.

## Folder index files are `README.md` (not `INDEX.md`)

Every folder under `agents/` uses a `README.md` as its index. Decided 2026-06-14: keep
`README.md`, **not** `INDEX.md`, for per-directory indexes.

- GitHub/GitLab **auto-render `README.md`** when you open *any* directory — the folder's
  "welcome mat". `INDEX.md` gets no such treatment. Since `agents/` is read directly in
  the repo (by humans and assistants), that auto-render is the main benefit.
- Per-folder `README.md` is the established convention (Google doc styleguide; GitHub UX).
  `index.md`/`INDEX.md` is a static-site-generator concept (MkDocs/Hugo) — and `agents/`
  is not a generated site.
- No conflict with the repo-root project `README.md`: GitHub shows the `README.md` of the
  folder you're in; the root one describes the project, each `agents/**/README.md` indexes
  its folder. Same filename, different directories, distinct purpose.

## Why `agents/` at the repo root (not `docs/dev/agents/`)

Decided 2026-06-14. These are **agent artifacts, not project documentation** — `docs/` is
user/project-facing (it also hosts a Next.js site); putting AI tooling there conflated two
audiences and, worse, forced a split between a tool's *spec* (in `docs/`) and its
*executable code* (which can't live in `docs/`). A root `agents/` lets a tool's spec and
code sit together.

**Practices compared (2025–2026):**
- **AGENTS.md at repo root** is the de-facto cross-tool standard. We keep it.
  ([AGENTS.md guide](https://blog.buildbetter.ai/agents-md-complete-guide-for-engineering-teams-in-2026/))
- **Anthropic "Agent Skills" standard**: a skill is a folder with `SKILL.md` plus optional
  `scripts/` (code) — **code and docs live together**. We adopt this for `tools/`: the
  code package is the tool, its docstring is the doc; a `.md` spec is added only for
  MCP/external tools whose config isn't in the code (a self-documenting `python -m`
  package gets no `.md` — that would just duplicate the docstring).
  ([SKILL.md standard](https://www.agensi.io/learn/agent-skills-open-standard),
  [Claude docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview))
- **Repository-based convention** groups agentic tooling under a root `agents/` with
  `skills/` etc. — which is what we do.
  ([agent-ready repo](https://medium.com/@huseyinkaplandev/agent-ready-repo-structure-2026-90af2ac8aed2))
- Test-only helpers (fixture trimming, the HTTP mock) are **not** agent tools — they live
  in `tests/utils/` and are imported by `conftest`. A tool that hits live APIs to refresh
  fixtures (`agents/tools/exchange_fixtures`) reuses `alphavar.exchange` (never
  re-implements requests) and is run on demand.

## Options considered

1. **`agents/` at repo root, spec+code together (chosen).** Matches the Agent-Skills
   standard; one home for AI artifacts, separate from user docs; a tool's spec and code
   sit together. Multi-LLM, team- and Windows-friendly.
2. **Keep `docs/dev/agents/` (specs) + a separate root code dir.** Rejected: splits a
   tool's spec from its code; `docs/` is the wrong audience for agent artifacts.
3. **Neutral top-level `ai/` umbrella with a sync step.** Most tool-agnostic but adds a
   build/sync step to keep vendor copies in lockstep — rejected as premature.
4. **Everything under `.claude/`.** Rejected: Claude-only, unreadable by the other
   LLMs/tools the team uses, and AGENTS.md-ecosystem tools ignore it.

## Status

The model is the decision to record; populate `skills/`/`tools/` as concrete ones emerge.
First tool: `tools/exchange_fixtures/` (records exchange API fixtures for hermetic tests).
