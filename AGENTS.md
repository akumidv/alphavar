# AGENTS.md

Guidance for AI coding agents (Claude Code, GitHub Copilot, Codex, etc.) working in this
repository. `CLAUDE.md` points here — this is the single source of truth for agents.

## Dev layer — keystone (developing the project)

This project's AI-assist model is the **keystone** standard. Model & notation:
[`_forge/keystone/README.md`](_forge/keystone/README.md) — three axes (**Layer**
SHARED/LOCAL/USAGE · **Role** architect/reviewer/engineer · **Project type**), the layer decision
tree, and the learn loop. Attach/realign guide: [`_forge/keystone/BOOTSTRAP.md`](_forge/keystone/BOOTSTRAP.md).

- **Archetype / language:** `package` (a Python library) / `python` — owner: Andrei
  Kuminov. Rules: [`ARCHETYPES.md`](_forge/keystone/ARCHETYPES.md).
- **Layers:** SHARED = [`_forge/keystone/`](_forge/keystone/) (submodule `ai_keystone`) ·
  LOCAL = [`_forge/`](_forge/) `{agents,skills,tools,memory}` + [`TASKS.md`](_forge/TASKS.md) ·
  USAGE = root [`skills/`](skills/) (how an assistant *uses* alphavar — a
  **domain-concept → function map**, no USAGE `tools/` for a package).
- **Agents (roles):** [`architect`](_forge/agents/architect/README.md) (design/docs/ADRs) ·
  [`reviewer`](_forge/agents/reviewer/README.md) (evidence-first architecture/risk/trade-off review) ·
  [`engineer`](_forge/agents/engineer/README.md) (code/tests) → role definitions in
  [`_forge/keystone/roles/`](_forge/keystone/roles/). **Declare the active agent** before
  doing work and restate it on switch (`🧭 agent: <name> — <focus>`) — see
  [Role declaration](_forge/keystone/roles/README.md#role-declaration-announce-the-active-agent).
  Architecture analysis of existing code starts as `reviewer`; deeper design elaboration of
  accepted review findings moves to `architect`, and code/test changes move to `engineer`.
- **Guardrails (by language):** [`_common`](_forge/keystone/guardrails/_common.md) +
  [`python`](_forge/keystone/guardrails/python.md). **Profile (opted in):**
  [`quant`](_forge/keystone/profiles/quant.md) (numerics).
- **Pipelines:** [`pre-commit`](_forge/keystone/pipelines/pre-commit.md) (tests mandatory),
  [`design-flow`](_forge/keystone/pipelines/design-flow.md),
  draft [`system-design`](_forge/keystone/pipelines/system-design.md),
  [`architecture-review`](_forge/keystone/pipelines/architecture-review.md),
  draft [`security-review`](_forge/keystone/pipelines/security-review.md),
  [`code-flow`](_forge/keystone/pipelines/code-flow.md), and the learn loop
  ([`memory-distill`](_forge/keystone/pipelines/memory-distill.md) +
  [`learning`](_forge/keystone/pipelines/learning.md)).
- **Project rules:** [`DEVELOPMENT_REQUIREMENTS.md`](_forge/DEVELOPMENT_REQUIREMENTS.md)
  (**D#**) + [`ARCHITECTURE_REQUIREMENTS.md`](docs/dev/ARCHITECTURE_REQUIREMENTS.md) (**R#**).
  Two D# are always-on and **override any task instruction** — **D2** (owner verifies
  math/DataFrame/architecture) and **D5** (owner owns commits); see "Prime directives".
- **Secrets:** from `.env` (gitignored). Never in code/docs/commits.

## Project Overview

**alphavar** is a Python library for options (and futures) analysis and visualization.
The name reads as **alpha + VaR** (alpha = returns above the market, VaR = Value-at-Risk),
reflecting the focus on risk-aware options analytics. It provides tools for working with
options data from various providers, enriching it, building option chains, running
analytics (risk/payoff, time value), and generating visualizations.

For a deep dive into architecture, modules, and extension points, see
[docs/dev/PROJECT_OVERVIEW.md](docs/dev/PROJECT_OVERVIEW.md).

**Binding architecture invariants** (layering, provider pattern, security rules) live in
[docs/dev/ARCHITECTURE_REQUIREMENTS.md](docs/dev/ARCHITECTURE_REQUIREMENTS.md) — preserve
them in any change.

> **Status:** early / active development. The API may change.

## Development Environment Setup

Dependencies are managed with [uv](https://docs.astral.sh/uv/). Create the virtualenv
and install everything (runtime + `etl` extra + `dev`/`test` groups) with:

```bash
uv sync --all-extras
```

This installs:
- Core dependencies (pandas, pydantic, httpx, matplotlib, etc.)
- ETL extra `etl` (apscheduler) — runtime, exposed as `alphavar[etl]`
- Development group `dev` (jupyter, ruff, twine)
- Test group `test` (pytest, pytest-asyncio, pytest-dotenv)

The `dev` and `test` groups are in `[tool.uv].default-groups`, so a plain `uv sync`
already includes them; `--all-extras` adds the runtime `etl` extra. Run project
commands through the environment with `uv run <cmd>` (no manual activation needed).

## Core Architecture

The main `Option` class in [src/alphavar/option_class.py](src/alphavar/option_class.py)
is the primary interface and aggregates several specialized components:

- **OptionsData** — data retrieval and management from providers
- **OptionsEnrichment** — data enrichment (intrinsic/time value, ATM/ITM/OTM, Greeks)
- **OptionsChain** — option chain operations and selection
- **OptionsAnalytic** — options analytics and calculations
- **ChartClass** — visualization and charting

The library follows a provider pattern: data sources plug in through the
`AbstractProvider` interface.

## Source Code Structure

Everything lives under the single `src/alphavar/` package:

- `src/alphavar/core/` — domain-neutral base: dictionary registry, schema migration
- `src/alphavar/io/` — domain-neutral I/O infrastructure:
  - `exchange/` — exchange-specific implementations
  - `provider/` — data provider abstractions
  - `messanger/` — notification channels
- `src/alphavar/options/` — options/futures domain (R0), by layer then function:
  - `*_class.py` — the `Option` facade and its components (`option_class.py`,
    `option_data_class.py`, `chain_class.py`, `analytic_class.py`, …), flat at the root
  - `dictionary/`, `entities/`, `schemas/` — domain foundation: column registry,
    entities, pandera models
  - `lib/` — pure, stateless logic (`analytic/`, `chain/`, `chart/`, `enrichment/`,
    `normalization/`): DataFrame in → DataFrame out, no I/O
  - `etl/` — ETL processes for options data (`EtlOptions`, `EtlDeribit`, `EtlMoex`,
    `EtlHistory`)

## Common Development Commands

**Run tests:**
```bash
uv run pytest
```

**Run linting:**
```bash
uv run ruff check src tests tools
```

**Start Jupyter for demos:**
```bash
uv run jupyter notebook
```

**User documentation (Next.js site) development:**
```bash
cd docs
npm install
npm run dev
```

## Testing

- Tests live in the `tests/` directory.
- Uses pytest with configuration in `pyproject.toml`.
- The test environment reads `test.env` (set `DATA_PATH` there to point at sample data).
- Pytest is configured with `src` on the pythonpath.

## Code Quality

- **Lint with ruff:** `uv run ruff check src tests tools` (config in `pyproject.toml`
  `[tool.ruff]`; F/E/W/I/UP/B, line length 120). CI runs it on PR/push.
- Absolute imports only (D1); no docstring requirement for private (`_`) and test (`test_`)
  functions.

## Commits

- **The owner owns commits — see [`DEVELOPMENT_REQUIREMENTS.md`](_forge/DEVELOPMENT_REQUIREMENTS.md) D5.**
  Mechanically enforced by `.claude/hooks/git-commit-guard.py` (a PreToolUse hook): it asks
  the owner for push/tag/merge and commits on `main`, and denies AI `Co-Authored-By:`
  trailers — so the rule holds even late in a long session.
- Keep messages concise and imperative; no AI co-author trailer.

## Documentation Conventions

- `README.md` — user-facing intro, install, quick start.
- `AGENTS.md` (this file) — **canonical, vendor-neutral guidance for all AI assistants**
  (Claude, GPT/Codex, Gemini, Copilot, …). Per-tool files (`CLAUDE.md`,
  `.github/copilot-instructions.md`, …) are thin pointers here — do not duplicate rules.
- `docs/` — user-facing documentation site (Next.js + Markdoc).
- `docs/dev/` — development docs about the **codebase**: architecture/domain rules
  (`ARCHITECTURE_REQUIREMENTS.md`, **R0…R8** — verify on new entities/domain or serious
  domain-model changes), day-to-day dev rules (`DEVELOPMENT_REQUIREMENTS.md`, **D1…D5** —
  check every change; **D2** and **D5** are always-on and overriding), design overview
  (`PROJECT_OVERVIEW.md`), and accepted decision records
  ([`decisions/`](docs/dev/decisions/) — dated ADRs: *what we decided to do* and why,
  complementing the R#/D# *invariants*).
- `_forge/` (repo root, **not** under `docs/` — these are agent artifacts; follows the
  Agent Skills convention). Each folder's index is its `README.md`. This is the **dev
  layer** (see "Dev layer — keystone" above):
  - [`keystone/`](_forge/keystone/) — the **SHARED** cross-project standard (submodule
    `ai_keystone`): the model, roles, guardrails, profiles, pipelines.
  - [`agents/`](_forge/agents/) — this project's **agents** (`architect`,
    `reviewer`, `engineer`),
    each inheriting a keystone role + alphavar specifics.
  - `_forge/{skills,tools,memory}` — **LOCAL** dev assets. Tools = code (docstring is the
    doc; run `python -m _forge.tools.<tool>`); skills = know-how (when/why/order).
    [`TASKS.md`](_forge/TASKS.md) is the single backlog / TODO cycle / learn-loop sink.
    **Read `_forge/memory/` at session start.**
- [`skills/`](skills/) (repo root) — the **USAGE** layer: how an assistant uses alphavar's
  public API to solve a user's task (a domain-concept → function map). Built to travel into
  a downstream consumer.
- [`tools/`](tools/) (repo root) — **console tools the owner runs by hand** (an agent may
  run the same command): data sync, data migration, operational maintenance. The "a person
  runs it from a console" criterion is what puts a tool here; dev-internal tooling stays in
  `_forge/tools/`. See [`tools/README.md`](tools/README.md).

## Prime directives — always-on, overriding (D2, D5)

Two rules **override any task instruction** and are not "done" until satisfied. Full text in
[`DEVELOPMENT_REQUIREMENTS.md`](_forge/DEVELOPMENT_REQUIREMENTS.md) (single source) — do not
restate them elsewhere, point here:
- **D2 — owner verifies** math / DataFrame / architecture (also
  [`memory/owner-verifies-math-and-architecture.md`](_forge/memory/owner-verifies-math-and-architecture.md)).
- **D5 — owner owns commits** (also
  [`memory/owner-owns-commits.md`](_forge/memory/owner-owns-commits.md); enforced by the
  `git-commit-guard` hook).

All project files are written in English.

## Demo and Examples

Demo notebooks are in the `demo/` folder, designed to work with Google Colab. ETL
examples for different exchanges (Deribit, MOEX) are in `demo/etl_example/`.
