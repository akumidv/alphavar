# Build vs operate agents: layout, modes, requirement axes

**Decided 2026-06-15.** The `agents/` tree separates agents by **what they act on**, adds a
default operating mode, and places each rule-set with its subject.

**Two classes + substrate:**
- `_dev/` — the **build** agent (underscore = private/special): edits the codebase. Bound by
  R# + D#.
- `desk/` — the **operate** agents (trading desk): act on the market/data/money. Bound by
  G#. One folder per agent (charter + pipeline + `skills/ tools/ memory/`).
- `shared/` — substrate (knowledge now; shared skills/tools later) for both classes →
  exposed as MCP later.

**Modes (vendor-neutral).** Default = **desk**. Switch by plain-text signal
(`dev`/`build` ↔ `desk`/`operate`) declared in `AGENTS.md`; the assistant announces the
active mode at session start. Vendor sub-agent files (`.claude/agents/…`) are optional and
only *reference* the neutral charters — switching never depends on them.

**Three requirement axes, placed by subject (not all in `docs/dev/`):**
- R# (`docs/dev/ARCHITECTURE_REQUIREMENTS.md`) — about the code.
- D# (`docs/dev/DEVELOPMENT_REQUIREMENTS.md`) — about building the code (incl. the dev agent).
- G# (`agents/desk/GUARDRAILS.md`) — about operating the desk fleet at runtime. Guardrails
  live **with the agents they govern**, not in `docs/dev/` (which is library/dev docs).
  `AGENTS.md` indexes all three regardless of location.

**TASKS** returns into the repo at `agents/_dev/TASKS.md` (the dev agent's TODO cycle and
the learn-loop sink), not `docs/dev/`.

**Learn loop.** Desk agent → key action/insight into its `memory/` → build agent (under
R#/D#, via `_dev/TASKS.md`) reworks it into skills/tools/code, or graduates it into
`shared/knowledge/`. The ecosystem improves itself *through* the build agent, never by
self-editing the codebase.

Supersedes the internal-layout part of
[agent-artifacts-layout.md](agent-artifacts-layout.md) (the root-`agents/` decision still
holds). Full model: [agents/README.md](../../README.md).
