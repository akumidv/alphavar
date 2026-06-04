# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python library for options trading analysis and visualization called "options_assembler". The library provides tools for working with options data from various providers, performing analytics, creating option chains, and generating visualizations.

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

The main `Option` class in `src/options_assembler/option_class.py` serves as the primary interface and aggregates several specialized components:

- **OptionData**: Handles data retrieval and management from providers
- **OptionEnrichment**: Provides data enrichment capabilities
- **OptionChain**: Manages option chain operations and selection
- **OptionAnalytic**: Performs options analytics and calculations
- **ChartClass**: Handles visualization and charting

The library follows a provider pattern where different data sources can be plugged in through the `AbstractProvider` interface.

## Source Code Structure

- `src/options_lib/` - Core library functionality including:
  - `entities/` - Data entities and enums
  - `chain/` - Option chain processing
  - `normalization/` - Data normalization utilities
- `src/options_assembler/` - Main assembler components
- `src/exchange/` - Exchange-specific implementations
- `src/provider/` - Data provider abstractions
- `src/options_etl/` - ETL processes for options data

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

**Documentation development:**
```bash
cd docs
npm install
npm run dev
```

## Testing

- Tests are located in the `tests/` directory
- Uses pytest with configuration in `pyproject.toml`
- Test environment uses `test.env` file for configuration
- Pytest is configured with `src` in pythonpath

## Code Quality

- Pylint configuration in `pyproject.toml` with 120 character line limit
- Protected access allowed for test functions (prefix `test_`)
- No docstring requirements for private (`_`) and test (`test_`) functions

## Demo and Examples

Demo notebooks are available in the `demo/` folder, designed to work with Google Colab. ETL examples for different exchanges (Deribit, MOEX) are in `demo/etl_example/`.