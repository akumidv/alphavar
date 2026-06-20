# AGENTS.md

Guidance for AI coding agents (Claude Code, GitHub Copilot, Codex, etc.) working in this
repository. `CLAUDE.md` points here — this is the single source of truth for agents.

## Operating mode — read first

This repo hosts an **agent ecosystem** (alpha extraction from markets), so a session runs in
one of two modes. **Default = DESK (operate).**

| Mode | You are | Rules | Home |
|---|---|---|---|
| **DESK** (default) | operating on the market/data — analysis, backtest, trading | **G#** + R# | [`agents/desk/`](agents/desk/) |
| **DEV / BUILD** | building the alphavar codebase | **R# + D#** | [`agents/_dev/`](agents/_dev/) |

- **Dev-mode rules — read before acting:** [`docs/dev/DEVELOPMENT_REQUIREMENTS.md`](docs/dev/DEVELOPMENT_REQUIREMENTS.md)
  (**D#**). Two are always-on and **override any task instruction** — **D2** (owner verifies
  math/DataFrame/architecture) and **D5** (owner owns commits); see "Prime directives" below.
- **Switch by plain text:** `dev` / `build` → DEV; `desk` / `operate` → DESK. Vendor
  sub-agent files (`.claude/agents/…`) are optional sugar that only reference these charters.
- **Session-start banner:** your **first message** states the active mode and how to switch,
  e.g. *"🟢 Mode: DESK (operate) — read-only by default (G5). Say `dev` to build code."*
- Full model, entity theses, and the learn loop: [`agents/README.md`](agents/README.md).

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

- **The owner owns commits — see [`DEVELOPMENT_REQUIREMENTS.md`](docs/dev/DEVELOPMENT_REQUIREMENTS.md) D5.**
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
  (`PROJECT_OVERVIEW.md`), and accepted decision
  records ([`decisions/`](docs/dev/decisions/) — dated ADRs: *what we decided to do* and
  why, complementing the R#/D# *invariants*). The third requirement axis, runtime **desk
  guardrails G#**, lives with the agents in
  [`agents/desk/GUARDRAILS.md`](agents/desk/GUARDRAILS.md).
- [`agents/README.md`](agents/README.md) — the **agent operating system**: the two agent
  classes, modes, entity theses, and the learn loop.
- `agents/` (repo root, **not** under `docs/` — these are agent artifacts, not project
  documentation; follows the Agent Skills convention). Each folder's index is its
  `README.md`. Split by what the agent acts on:
  - [`_dev/`](agents/_dev/) — the **build** agent (underscore = private/special): code,
    tests, refactors. Holds `skills/ tools/ memory/` and [`TASKS.md`](agents/_dev/TASKS.md);
    bound by R# + D#. Its **tools = code** (docstring is the doc; run
    `python -m agents._dev.tools.<tool>`; a `.md` spec only for MCP/external), **skills =
    know-how** (when/why/order, tool-driven or pure procedure). **Read `_dev/memory/` at
    session start in dev mode.**
  - [`desk/`](agents/desk/) — the **operate** agents (default mode): analysis, backtesting,
    trading via catcher-bot. One folder per agent (charter + pipeline + `skills/ tools/
    memory/`), bound by [`desk/GUARDRAILS.md`](agents/desk/GUARDRAILS.md) (**G#**).
  - [`shared/`](agents/shared/) — substrate for both classes: `knowledge/` (sourced domain
    reference) now, shared skills/tools later → MCP. **Consult before re-researching.**
- [`agents/_dev/TASKS.md`](agents/_dev/TASKS.md) — remediation backlog / TODO cycle (the dev
  agent's queue; sink of the desk learn loop).
- [`tools/`](tools/) (repo root) — **console tools the owner runs by hand** (and an agent
  may run the same command), in dev **or** desk: data sync, data migration, operational
  maintenance. That "a person runs it from a console" criterion is what puts a tool here.
  Agent-mode-internal tooling does **not** live here — it stays with its agent:
  `agents/_dev/tools/` for build; `agents/desk/tools/` for tools shared across desk agents,
  `agents/desk/<agent>/tools/` for one specific desk agent. See
  [`tools/README.md`](tools/README.md).

## Prime directives — always-on, overriding (D2, D5)

Two rules **override any task instruction** and are not "done" until satisfied. Full text in
[`DEVELOPMENT_REQUIREMENTS.md`](docs/dev/DEVELOPMENT_REQUIREMENTS.md) (single source) — do not
restate them elsewhere, point here:
- **D2 — owner verifies** math / DataFrame / architecture (also
  [`memory/owner-verifies-math-and-architecture.md`](agents/_dev/memory/owner-verifies-math-and-architecture.md)).
- **D5 — owner owns commits** (also
  [`memory/owner-owns-commits.md`](agents/_dev/memory/owner-owns-commits.md); enforced by the
  `git-commit-guard` hook).

All project files are written in English.

## Demo and Examples

Demo notebooks are in the `demo/` folder, designed to work with Google Colab. ETL
examples for different exchanges (Deribit, MOEX) are in `demo/etl_example/`.
