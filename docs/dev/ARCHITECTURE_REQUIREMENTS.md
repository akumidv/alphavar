# Architecture Requirements — alphavar

> **Status: binding.** This document captures the current architecture as a set of
> requirements. Any change (human or AI-agent) MUST preserve these invariants unless the
> document itself is explicitly revised first. Companion documents:
> [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) (descriptive overview) and
> [TASKS.md](TASKS.md) (remediation backlog).

## R1. Three-layer separation (core invariant)

```
alphavar facade (stateful)  →  options_lib (pure functions)  →  provider/exchange (I/O)
```

1. **`src/alphavar/` (facade layer)** — stateful classes only: `Option`, `OptionData`,
   `OptionEnrichment`, `OptionChain`, `OptionAnalytic`, `ChartClass`. They hold
   DataFrames, the provider reference, and request parameters. They contain **no
   computational business logic** — they orchestrate and delegate.
2. **`src/alphavar/options_lib/` (logic layer)** — pure, stateless functions and
   Pydantic entities: `DataFrame` in → `DataFrame` out. **No I/O, no network, no
   provider/exchange imports, no global mutable state.**
3. **`src/alphavar/provider/` + `src/alphavar/exchange/` (data layer)** — the only place
   where I/O happens (files, HTTP). Exchanges implement `AbstractProvider` (via
   `AbstractExchange`).

Dependency direction is one-way: facade → logic → (data via injected provider).
`options_lib` must never import from `alphavar` facade modules, `provider`, or
`exchange`.

## R2. Provider pattern

- Every data source implements `AbstractProvider`
  (`provider/_abstract_provider_class.py`): `get_assets_list`,
  `get_asset_history_years`, `load_options_history`, `load_options_book`,
  `load_futures_history`, `load_futures_book`, `load_options_chain`.
- File-based sources extend `AbstractFileProvider`; HTTP exchanges extend
  `AbstractExchange` and are registered in `ExchangeFabric` /
  `ExchangeProviderFactory`.
- The `Option` facade receives the provider by constructor injection and never
  instantiates providers itself.
- Request scoping goes through the `RequestParameters` Pydantic model — no ad-hoc
  parameter dicts.

## R3. Facade composition

- `Option` aggregates components that all share a single `OptionData` instance
  (dependency injection of shared state). New capability areas (pricer, forecast,
  validation) follow the same pattern: a component class taking `OptionData` in its
  constructor, exposed as an attribute of `Option`.

## R4. Data dictionary discipline

- DataFrame column names, option types, price statuses, asset kinds, timeframes, and
  currencies are referenced **only** through the enums in
  `options_lib/dictionary/` (`OptionsColumns`, `FuturesColumns`, `SpotColumns`,
  `OptionsType`, `Timeframe`, …). String literals for columns are forbidden.
- A new computed column requires: an `OptionsColumns` entry, the pure function in
  `options_lib/enrichment/`, an entry in `OPTION_COLUMNS_DEPENDENCIES` when it depends
  on other columns, and wiring in `OptionEnrichment`.

## R5. Packaging

- Single distributable package: `alphavar`, rooted at `src/alphavar/` (Poetry,
  `packages = [{ include = "alphavar", from = "src" }]`). No second top-level package
  may live under `src/`.
- Every `import` used by shipped code must be a declared dependency (direct, not
  transitive). Subpackages shipped in the wheel that need optional dependencies
  (e.g. `options_etl` → `apscheduler`) must map to a pip **extra**, and their imports
  must fail with an actionable error message.

## R6. ETL isolation

- ETL (`alphavar/options_etl/`) consumes exchanges through the same
  `AbstractExchange` interface; it never talks to HTTP endpoints directly.
- ETL writes update snapshots under
  `{update_data_path}/{EXCHANGE}/{ASSET}/{asset_kind}/{timeframe}/...parquet`; history
  layout is `{EXCHANGE}/{ASSET}/{asset_kind}/{timeframe}/{year}.parquet`. Providers and
  ETL must agree on this layout — change it only in both places at once.
- Notifications go through `AbstractMessanger`; ETL code must not depend on a concrete
  messenger.

## R7. Security requirements

- **No secrets in the repository** — tokens/keys only via environment variables
  (`TG_BOT_TOKEN`, `TG_CHAT`, …). `test.env` stays gitignored; a committed
  `test.env.example` documents the variables without values.
- Secrets must never appear in logs, exception messages, or report texts (incl. URLs
  containing tokens).
- Any value interpolated into a filesystem path (`asset_code`, `asset_name`,
  `exchange_code`, timeframe) must be validated against an allowlist pattern before
  use — no path traversal through data-derived names.
- All outbound HTTP uses explicit timeouts; public-only API usage is the default. If
  authenticated endpoints are ever added, request signing lives in `RequestClass`
  behind an explicit, tested code path — never per-exchange ad-hoc signing.
- Only HTTPS endpoints for exchange APIs.

## R8. DataFrame engine strategy: Polars as the target

- **Strategic direction: Polars is the target dataframe engine** (Rust core; enables
  interop with related Rust projects). pandas is the current engine; the codebase must
  not deepen its pandas lock-in.
- The column dictionary (`options_lib/dictionary/`) is **engine-neutral**: it defines
  plain string names and engine-agnostic metadata. It must not import pandas/polars
  types as part of its public contract (engine-specific dtype mapping lives next to the
  schemas, not in the name registry).
- DataFrame schemas (pandera) are defined per engine behind a common naming registry:
  `pandera.pandas` today, `pandera.polars` on migration — column names and checks carry
  over unchanged.
- New code in `options_lib` should prefer constructs with direct polars equivalents
  (column-wise expressions, joins, group-by aggregations) and avoid hard-to-port idioms
  (row-wise `df.apply`, implicit index reliance, `inplace=True` mutation chains).
- Engine selection goes through the existing `DataEngine` enum
  (`provider/_provider_entities.py`); providers receive the engine explicitly.

## R9. Quality gates

- Tests live in `tests/unit/<area>/`, mirroring `src/alphavar/`. Unit tests must be
  hermetic: no live network calls (HTTP is mocked), no machine-specific absolute paths.
- `pytest` and `pylint src/` must pass before merging to `main`.
- Python ≥ 3.11, line length ≤ 120, Pydantic models for entities/parameters,
  docstrings required except `_private`/`test_` functions.
- All project files in English.
