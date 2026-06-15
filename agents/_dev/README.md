# `_dev/` — the build agent (charter)

**Role.** The single agent that **builds and maintains the alphavar codebase**: writes and
refactors code, fixes and adds tests, keeps the architecture honest. The underscore marks
it *private/special* — it is the only agent that edits this repository.

**Mode.** `dev` / `build`. Not the default — a session enters it by the explicit text
signal (see [`../README.md`](../README.md) → Modes & switching). The default session mode
is **desk**.

**Bound by** (canonical, in `docs/dev/`, indexed by [`../../AGENTS.md`](../../AGENTS.md)):
- [`ARCHITECTURE_REQUIREMENTS.md`](../../docs/dev/ARCHITECTURE_REQUIREMENTS.md) — **R#**:
  layering, provider pattern, domain model, the column dictionary/naming.
- [`DEVELOPMENT_REQUIREMENTS.md`](../../docs/dev/DEVELOPMENT_REQUIREMENTS.md) — **D#**:
  day-to-day process. Especially **D2** — any math / DataFrame / architecture change must
  be explained and **explicitly verified by the owner**; passing tests are not enough.

> The build agent's guardrails are **D#**, *not* the desk **G#** — G# governs runtime market
> actions, which this agent never performs.

## Contents

- [`TASKS.md`](TASKS.md) — the remediation backlog and **TODO cycle**. Also the **sink of
  the learn loop**: insights a desk agent records in its memory are triaged into tasks here,
  then implemented under R#/D#.
- [`skills/`](skills/) — build playbooks (e.g. refresh exchange fixtures, add an exchange
  source).
- [`tools/`](tools/) — deterministic code tools (e.g. the exchange-fixtures recorder),
  reusing `alphavar.*` rather than re-implementing it (D4).
- [`memory/`](memory/) — durable notes on *how we build this project* (env, decisions).
  **Read at session start.** Stable items graduate into R#/D#.

## Learn loop (build side)

A desk agent finds an insight/weakness → writes it to its own `memory/findings.md`. The
build agent triages it: if it is **knowledge** → graduate into
[`../shared/knowledge/`](../shared/knowledge/); if it is **work** → a task in
[`TASKS.md`](TASKS.md) → implement as code/skill/tool under R#/D# (with D2 owner
verification for any math/DataFrame/architecture). This is how the ecosystem improves
itself — *through* the build agent, never by self-editing the codebase.
