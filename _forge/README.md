# `_forge/` — the alphavar dev layer

The **development** layer for this project (the "forge" where the project is built). It
follows the **keystone** standard — model and notation in
[`keystone/README.md`](keystone/README.md). The project entry point is the root
[`AGENTS.md`](../AGENTS.md).

> `_forge/**` = developing this project · `_forge/keystone/**` = the SHARED (cross-project)
> subset · root `skills/` = using the project (USAGE). See keystone README §2.

## Contents

- [`keystone/`](keystone/) — **SHARED** cross-project standard (submodule `ai_keystone`):
  the model, [`roles/`](keystone/roles/), [`guardrails/`](keystone/guardrails/),
  [`profiles/`](keystone/profiles/), [`pipelines/`](keystone/pipelines/).
- [`agents/`](agents/) — this project's **agents**: [`architect`](agents/architect/README.md)
  (design/docs/ADRs) and [`engineer`](agents/engineer/README.md) (code/tests), each
  inheriting a keystone role + alphavar specifics.
- [`skills/`](skills/) — **LOCAL** dev playbooks (refresh fixtures, add an exchange source,
  migrate stored data, track a task).
- [`tools/`](tools/) — **LOCAL** dev tools (code; run `python -m _forge.tools.<tool>`):
  `exchange_fixtures` (recorder), `data_migration` (verify + fix stored data).
- [`memory/`](memory/) — **SHARED project memory** (in git): durable notes on how we build
  this project. **Read at session start.**
- [`design/`](design/) — in-progress **design concepts** (architect role): living concept,
  rejected branches, design backlog. Folded into an ADR once locked.
- [`TASKS.md`](TASKS.md) — the single backlog / TODO cycle / learn-loop sink.
- [`DEVELOPMENT_REQUIREMENTS.md`](DEVELOPMENT_REQUIREMENTS.md) (**D#**) + the
  [`D2_VERIFICATION.md`](D2_VERIFICATION.md) ledger — the **development process** (how we
  build), kept here in the dev layer; the project's *architecture* (R#, ADRs, overview)
  stays in [`../docs/dev/`](../docs/dev/) (what a new developer reads to understand the
  project).

## Bound by

- **R#** — [`../docs/dev/ARCHITECTURE_REQUIREMENTS.md`](../docs/dev/ARCHITECTURE_REQUIREMENTS.md)
  (layering, provider pattern, domain model, column dictionary) — stays in `docs/dev/`.
- **D#** — [`DEVELOPMENT_REQUIREMENTS.md`](DEVELOPMENT_REQUIREMENTS.md)
  (day-to-day process; **D2** owner-verify, **D5** owner-owns-commits are always-on).
- Language [`guardrails/`](keystone/guardrails/) (python) + the opted-in
  [`quant`](keystone/profiles/quant.md) profile.

## Learn loop

An agent records an insight to [`memory/`](memory/); recurring facts distill into a LOCAL
skill/tool/agent or a requirement/ADR; proven, general assets are **promoted into keystone**
(PR → `ai_keystone`) so every project inherits them. Full mechanics:
[`keystone/pipelines/memory-distill.md`](keystone/pipelines/memory-distill.md) +
[`learning.md`](keystone/pipelines/learning.md).
