# AGENTS.md

Guidance for AI coding agents (Claude Code, GitHub Copilot, Codex, etc.) working in this
repository. `CLAUDE.md` points here — this is the single source of truth for agents.

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
- Development group `dev` (jupyter, pylint, twine)
- Test group `test` (pytest, pytest-asyncio, pytest-dotenv)

The `dev` and `test` groups are in `[tool.uv].default-groups`, so a plain `uv sync`
already includes them; `--all-extras` adds the runtime `etl` extra. Run project
commands through the environment with `uv run <cmd>` (no manual activation needed).

## Core Architecture

The main `Option` class in [src/alphavar/option_class.py](src/alphavar/option_class.py)
is the primary interface and aggregates several specialized components:

- **OptionData** — data retrieval and management from providers
- **OptionEnrichment** — data enrichment (intrinsic/time value, ATM/ITM/OTM, Greeks)
- **OptionChain** — option chain operations and selection
- **OptionAnalytic** — options analytics and calculations
- **ChartClass** — visualization and charting

The library follows a provider pattern: data sources plug in through the
`AbstractProvider` interface.

## Source Code Structure

Everything lives under the single `src/alphavar/` package:

- `src/alphavar/` — the `Option` facade and entry-point classes (`option_class.py`,
  `option_data_class.py`)
- `src/alphavar/core/` — domain-neutral base: dictionary registry, schema migration
- `src/alphavar/options/` — options/futures domain (R0 target home):
  - `dictionary/`, `schemas/` — column registry + pandera models
  - `etl/` — ETL processes for options data (`EtlOptions`, `EtlDeribit`, `EtlMoex`,
    `EtlHistory`)
- `src/alphavar/options_lib/` — pure, stateless logic (entities, chain, normalization,
  analytics) — being migrated into `options/`
- `src/alphavar/exchange/` — exchange-specific implementations
- `src/alphavar/provider/` — data provider abstractions
- `src/alphavar/messanger/` — notification channels

## Common Development Commands

**Run tests:**
```bash
uv run pytest
```

**Run linting:**
```bash
uv run pylint src/
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

- Pylint configuration in `pyproject.toml` with a 120-character line limit.
- Protected access is allowed for test functions (prefix `test_`).
- No docstring requirements for private (`_`) and test (`test_`) functions.

## Documentation Conventions

- `README.md` — user-facing intro, install, quick start.
- `AGENTS.md` (this file) — **canonical, vendor-neutral guidance for all AI assistants**
  (Claude, GPT/Codex, Gemini, Copilot, …). Per-tool files (`CLAUDE.md`,
  `.github/copilot-instructions.md`, …) are thin pointers here — do not duplicate rules.
- `docs/` — user-facing documentation site (Next.js + Markdoc).
- `docs/dev/` — development documentation: architecture/domain rules
  (`ARCHITECTURE_REQUIREMENTS.md`, R0…R8 — verify on new entities/domain or serious
  domain-model changes), day-to-day dev rules (`DEVELOPMENT_REQUIREMENTS.md`, D1…D3 —
  check every change), design overview (`PROJECT_OVERVIEW.md`).
- `docs/dev/AI_WORKING_MODEL.md` — how AI-development artifacts are organized in-repo.
- `docs/dev/agents/` — vendor-neutral AI artifacts: `memory/` (durable notes →
  graduate into rules), `skills/` (task playbooks), `tools/` (tool/MCP specs — prefer
  tools as code to save tokens, D4), `knowledge/` (concentrated, sourced domain knowledge
  — exchanges/APIs, options, risk, portfolio). **Read `docs/dev/agents/memory/` at session
  start; consult `knowledge/` before re-researching the domain.**
- `Option_and_futures/TASKS.md` — remediation backlog (task statuses).

## Mandatory: owner verification of math / DataFrame / architecture

Any DataFrame operation, quantitative/financial math, or architectural change must be
explained and **explicitly verified by the owner** before it is "done" — passing tests
are not sufficient. See `DEVELOPMENT_REQUIREMENTS.md` **D2** and
`docs/dev/agents/memory/owner-verifies-math-and-architecture.md`.

All project files are written in English.

## Demo and Examples

Demo notebooks are in the `demo/` folder, designed to work with Google Colab. ETL
examples for different exchanges (Deribit, MOEX) are in `demo/etl_example/`.
