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

### R4.1 Naming: singular vs plural for `option`/`future`

`option`/`future` are domain entity names. The rule is grammatical, not stylistic:

- **Plural** (`options`/`futures`) for anything denoting a *category or collection*:
  asset-kind values stored in data (`AssetKind.OPTIONS = "options"` — already in
  parquet, do not change), dictionary classes (`OptionsColumns`, `FuturesColumns`),
  API method families (`load_options_history`, `load_futures_history`), package/path
  segments, and any variable holding a set/list/DataFrame of instruments
  (`options_df`, not `option_df`; `BookData.options`, not `.option`).
- **Singular** (`option`/`future`) **only** as a qualifier of one attribute of a
  single instrument: `option_type`, `option_style`, `option_symbol`,
  `future_expiration_date`. A bare singular `option`/`future` identifier is a smell —
  it almost always denotes a collection and should be plural.

There is currently no legitimate use of a bare singular `option`/`future` for a single
entity in the code; the few that exist (`BookData.option/.future`, the `option = []`
accumulator in `moex.py`) are collections and should be pluralized.

**Domain convention takes precedence over grammar.** In derivatives trading the asset
classes are *the options market* / *the futures market* — established industry usage
(CME, Databento, Xignite and other data APIs use the plural for the instrument class).
So the plural is the correct domain name, and it applies to **all identifier kinds**,
not just variables:

- **Packages / directories**: `options_lib`, `options_etl` (plural). A new asset-class
  area follows suit.
- **Files / modules**: name by the entity in its domain-correct form
  (`option_class.py` describes a single `Option` *instrument* → singular is fine;
  a module about the options *dataset/market* uses plural).
- **Classes**: `Option` (one instrument) is singular by design; `OptionsColumns`,
  `OptionsChain`, `OptionsAnalytic` (the options domain/collection) are plural.
- **Enums / values stored in data**: `AssetKind.OPTIONS = "options"` (plural, already
  in parquet).

Rule of thumb: *one contract* → `Option`/`Future` (singular); *the market, dataset,
column group, or any collection* → `options`/`futures` (plural). When in doubt, match
how exchanges and market-data APIs name it.

### R4.2 Price / IV column model

There are several independent price (and IV) concepts per instrument. They are
**distinct columns**, never overwritten into one another. Three groups:

**1. The project's own values (no prefix) — the headline columns.**
`PRICE` (`price`) / `IV` (`iv`) are **ours**, not the exchange's: the output of our
normalization pipeline (Black-Scholes pricing, volatility-smile fitting, arbitrage
removal). These are the canonical columns users consume; everything in the library
defaults to them. There is **no** separate `fair_*` pair — `price`/`iv` *are* our fair
value.

| Concept | Column | IV | Meaning |
|---|---|---|---|
| Our normalized value | `PRICE` (`price`) | `IV` (`iv`) | Output of our model (BS + smile fit + no-arbitrage). The library's default price/IV. |

**2. Real exchange values (`exch_` prefix) — what the venue actually published.**
Kept so our normalization is auditable and recomputable. An exchange publishes one fair
estimate, so Deribit `mark_price` and MOEX `theorprice` both map into the single
`exch_mark_*` pair (we do not split mark vs theoretical).

| Concept | Column | IV | Meaning |
|---|---|---|---|
| Exchange traded price | `EXCH_PRICE` (`exch_price`) | `EXCH_IV` (`exch_iv`) | The venue's traded/quoted price as received. |
| Exchange mark/estimate | `EXCH_MARK_PRICE` (`exch_mark_price`) | `EXCH_MARK_IV` (`exch_mark_iv`) | The venue's fair-value/mark estimate (Deribit `mark_price`, MOEX `theorprice`). An estimate, not a trade. |
| Settlement (EOD) | `SETTLE_PRICE` (`settle_price`) | `SETTLE_IV` (`settle_iv`) | Official daily clearing/settlement price. EOD-only; null intraday. Term is unambiguous, so no `exch_` prefix. |

`ask`/`bid`/`mid`/`last`/`high`/`low` keep their own columns; `price`/`iv` are never
mere copies of them.

**The `exch_` rule generalizes beyond price** to any field that holds a raw venue value
alongside our own derived one. Timestamps follow the same split:

| Concept | Column | Meaning |
|---|---|---|
| Our request moment | `REQUEST_TIMESTAMP` (`request_timestamp`) | When *we* fetched the snapshot (`pd.Timestamp.now`). Ours. |
| Exchange timestamp | `EXCH_TIMESTAMP` (`exch_timestamp`) | The venue's own timestamp on the record (Deribit `creation_timestamp`, MOEX `updatetime`). One column per venue value, like `exch_mark_*`. Renamed from the old `original_timestamp`. |
| Our normalized moment | `TIMESTAMP` (`timestamp`) | The working, normalized instant the library uses (rounded to 1s). Ours — no prefix. |

(Deribit `creation` vs MOEX `update` are different venue times conflated into
`exch_timestamp` today, mirroring the mark/theor case; splitting them is deferred.)

**3. Raw pre-transform values (`_raw` suffix) — narrow, only where we mutate.**
A `<col>_raw` column preserves an exchange value **before an irreversible transform we
apply**, so the transform can be reverted/recomputed. It is **not** a mirror of every
column. Today the only such transform is currency conversion in `deribit.py`
(multiplying by `estimated_delivery_price` to convert base→quote): the pre-conversion
value of each affected column (`ask`, `bid`, `last`, `high_24`, `low_24`,
`exch_mark_price`) is stored as `<col>_raw` (`ask_raw`, `exch_mark_price_raw`, …). Add
`<col>_raw` **only** when introducing a new irreversible per-exchange transform — not by
default. (Replaces the old `source_`/`SOURCE_PREFIX` prefix.)

The `_raw` **suffix** (not a prefix) is deliberate: it keeps a value and its raw form
adjacent under column sorting / prefix filtering (`exch_mark_price`,
`exch_mark_price_raw`), and matches the dictionary's existing suffix-as-modifier
pattern (`high_24`, `volume_notional`). A `source_` prefix would be the only prefixed
modifier and would scatter raw values into a separate namespace.

Short prefixes (`exch_`, `exch_mark_`, `settle_`) + the `_raw` suffix keep names compact
while explicit. Rationale: `price`/`iv` belong to the project (the value of the library
is the normalization), so they get the unprefixed names; raw venue data is explicitly
`exch_*`/`settle_*`; `mark` is the right domain term for an exchange estimate (vs
settlement = official EOD price). The old single `exchange_mark_price` had a typo
(`exhchange_…`) and conflated layers. Migration is covered in TASKS T23.6.

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
