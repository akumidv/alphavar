# AI agents — `agents/`

This directory is the project's **AI agent operating system**: the charters, knowledge,
skills, tools and memory for the assistants that **build** and **operate** the alphavar
ecosystem. It is kept in-repo (versioned, shared across the team and machines — incl.
Windows, no symlinks) and **LLM-agnostic**: plain Markdown/JSON any assistant (Claude,
GPT/Codex, Gemini, Copilot, …) or human can read. No vendor's tooling is privileged here;
the single entry point is the root [`AGENTS.md`](../AGENTS.md).

Canonical **rules** are not duplicated here — they live in `docs/dev/` and are indexed by
`AGENTS.md`: architecture `ARCHITECTURE_REQUIREMENTS.md` (**R#**), development
`DEVELOPMENT_REQUIREMENTS.md` (**D#**), and the desk runtime guardrails
[`desk/GUARDRAILS.md`](desk/GUARDRAILS.md) (**G#**).

## Two classes of agent

The ecosystem's mission is **alpha extraction** from financial markets (options/derivatives
now; equities, bonds, macro later), through the alphavar library plus the
[`catcher-bot`](https://github.com/akumidv/catcher-bot) trading bot. That splits the agents
by **what they act on** — not by domain:

| | **Build — [`_dev/`](_dev/)** | **Operate — [`desk/`](desk/)** |
|---|---|---|
| Acts on | the **codebase** | the **market / data / money** |
| Output | commits / PRs | analyses / signals / **orders** |
| Bound by | **R# + D#** (esp. **D2** owner-verify) | **G#** guardrails (+ R# for the data model) |
| Main risk | broken build | **lost money, silent wrong output** |
| Runs | during development (SDLC) | at runtime, possibly unattended / server-side |

- **`_dev/`** — underscore = *private/special*: it is the one agent that edits this repo.
- **`shared/`** — substrate (domain knowledge; later shared skills/tools) used by both
  classes, destined for an **MCP** server so the wider ecosystem can consume it.

## Modes & switching (vendor-neutral)

Mode selection lives entirely in `AGENTS.md` — no provider-specific feature required, so it
works identically on any LLM:

- **Default = DESK (operate).** A session starts on the desk unless told otherwise.
- **Switch by plain-text signal:** say `dev` / `build` → build mode (`_dev/`, rules R#+D#);
  say `desk` / `operate` → desk mode (rules G#).
- **Session-start banner:** the assistant's first message states the active mode and how to
  switch (so you are never unsure which mode is live).
- Optional vendor shims (`.claude/agents/*.md`, Cursor/Codex equivalents) only **reference**
  these charters — the switch never depends on them.

## Entity theses (what is what)

- **Agent** — a `README.md` charter (role, scope, success, guardrails) + a `pipeline` + the
  skills/tools/knowledge it binds + memory. One agent = one role.
- **Class** — `_dev` (build the system) vs `desk` (operate it). Differ by subject (code vs
  market), output (commit vs order), risk (broken build vs lost money).
- **Skill** — a playbook: *when / why / in what order*. **shared** (`shared/skills/`) or
  **agent-local** (`<agent>/skills/`). May call a tool or be pure procedure.
- **Tool** — code: deterministic, committed, reusable (D4). shared or agent-local. Reuses
  project code (`alphavar.*`, the catcher-bot client) — never re-implements it.
- **Knowledge** — concentrated, **sourced** domain reference. Always shared
  (`shared/knowledge/` → MCP). Agents consume it; they don't fork it per agent.
- **Memory** — durable learned notes. `_dev` = how-we-build; a desk agent = operating
  insights (the raw material of the learn loop).
- **Guardrail (G#)** — a hard runtime constraint for desk agents. Tiers: *global / class /
  agent*. Lives in [`desk/GUARDRAILS.md`](desk/GUARDRAILS.md).
- **Orchestrator** — head-of-desk: routes work across desk agents, enforces **separation of
  duties** (propose ≠ execute), produces the consolidated analysis.
- **Learn loop** — a desk agent saves a key action/insight to its `memory/`; the **build
  agent** (under R#/D#, via the TODO cycle in [`_dev/TASKS.md`](_dev/TASKS.md)) reworks it
  into skills/tools/code, or it graduates into `shared/knowledge/`. The ecosystem improves
  itself *through* the dev agent, not by self-editing the codebase.

## Layout

```
agents/
  README.md            # this file — agent OS overview, modes, entity theses
  _dev/                # BUILD agent (private/special) — builds alphavar itself
    README.md          #   charter (rules: R# + D#)
    TASKS.md           #   remediation backlog / TODO cycle / learn-loop sink
    skills/  tools/  memory/
  shared/              # cross-agent substrate (→ MCP later)
    knowledge/         #   sourced domain reference (exchanges, options, risk, portfolio)
  desk/                # OPERATE agents (default mode) — use alphavar + catcher-bot
    README.md          #   operating model, roster, orchestration
    GUARDRAILS.md      #   G# — desk runtime guardrails
    options-analyst/   #   one agent = charter + pipeline + skills/ tools/ memory/
    …                  #   investment-analyst, strategy-tester, fundamental-analyst, trader, orchestrator
```

## Conventions

- **Folder index = `README.md`** (GitHub auto-renders it — the folder's welcome mat).
  Decided 2026-06-14; not `INDEX.md` (a static-site-generator concept).
- **`agents/` at the repo root, not `docs/`** — these are agent artifacts, not project
  documentation, and code+spec sit together (Anthropic **Agent Skills** standard). Decision
  records: [`_dev/memory/agent-artifacts-layout.md`](_dev/memory/agent-artifacts-layout.md)
  and [`_dev/memory/agent-modes-and-layout.md`](_dev/memory/agent-modes-and-layout.md).
- Per-tool vendor files (`CLAUDE.md`, `.github/copilot-instructions.md`, …) are thin
  pointers to `AGENTS.md` — never a second source of truth.

**Practices compared (2025–2026):** [AGENTS.md as the cross-tool entry
point](https://blog.buildbetter.ai/agents-md-complete-guide-for-engineering-teams-in-2026/);
Anthropic [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
([open standard](https://www.agensi.io/learn/agent-skills-open-standard)) — a skill is a
folder with its doc + scripts together; a root `agents/` for agentic tooling.
