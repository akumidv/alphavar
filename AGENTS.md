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

> **Status:** early / active development. The API may change.

## Development Environment Setup

Install dependencies using Poetry (required for this project):

```bash
poetry install --with etl,dev,test
```

This installs:
- Core dependencies (pandas, pydantic, httpx, matplotlib, etc.)
- ETL dependencies (apscheduler)
- Development dependencies (jupyter, pylint)
- Test dependencies (pytest, pytest-asyncio)

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

- `src/options_lib/` — core library functionality:
  - `entities/` — data entities and enums
  - `chain/` — option chain processing
  - `normalization/` — data normalization utilities
- `src/alphavar/` — main assembler components (the `Option` facade)
- `src/exchange/` — exchange-specific implementations
- `src/provider/` — data provider abstractions
- `src/options_etl/` — ETL processes for options data

## Common Development Commands

**Run tests:**
```bash
pytest
```

**Run linting:**
```bash
pylint src/
```

**Start Jupyter for demos:**
```bash
jupyter notebook
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
- `AGENTS.md` (this file) — guidance for AI agents; `CLAUDE.md` links here.
- `docs/` — user-facing documentation site (Next.js + Markdoc).
- `docs/dev/` — development documentation: architecture, design decisions
  (`PROJECT_OVERVIEW.md`).

All project files are written in English.

## Demo and Examples

Demo notebooks are in the `demo/` folder, designed to work with Google Colab. ETL
examples for different exchanges (Deribit, MOEX) are in `demo/etl_example/`.
