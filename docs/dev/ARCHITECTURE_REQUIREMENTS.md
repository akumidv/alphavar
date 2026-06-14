# Architecture Requirements — alphavar

> **Status: binding.** This document captures the current architecture as a set of
> structural requirements (`R#`). Any change (human or AI-agent) MUST preserve these
> invariants unless the document itself is explicitly revised first. **Verify these
> especially when introducing new entities/domain concepts or making serious changes to
> the existing domain model.** For compact day-to-day development rules (quality gates,
> owner verification, workflow) see the companion
> [DEVELOPMENT_REQUIREMENTS.md](DEVELOPMENT_REQUIREMENTS.md) (`D#`). Descriptive overview:
> [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md). The remediation backlog is maintained
> outside this repository, alongside `ALPHAVAR_NAMING.md`.

## R0. Package layout: domain-first, then functional (target)

`alphavar` will grow beyond options/futures (equities, bonds, …). The top-level split is
therefore **by domain**, and *within* a domain by function (layer). A thin domain-neutral
base sits under the domains. This is the target layout; the current tree
(`options_lib`, `options_etl`, plus functional packages) migrates toward it.

```
alphavar/
  core/        # domain-NEUTRAL base: shared dictionary registry, normalization,
               #   base entities, schema mixins, path-safety. No domain math.
  io/          # data infrastructure, domain-neutral: provider/, exchange/, messanger/
  options/     # DOMAIN: options + futures (today's options_lib + options_etl, merged).
               #   Inside, by function: dictionary/ enrichment/ chain/ analytic/ chart/
               #   etl/ entities/ — plus the facade (Option and its components).
  equity/      # future domain (own math)
  bond/        # future domain
```

- **Why domain-first:** the math of options ≠ equities ≠ bonds; keeping each domain's
  logic, ETL and analytics together makes "add a new asset class = add a package"
  true, and a domain is visible from the tree (screaming architecture).
- **What stays neutral (not in a domain):** `core/` (shared identity/dictionary,
  normalization, base entities — see R4.x; "core + domain extensions") and `io/`
  (an exchange returns options, futures, and tomorrow equities — it is infrastructure,
  not a domain).
- **Naming:** the first domain keeps the recognizable name `options` (not
  `derivatives`), package `alphavar.options`. This aligns with the family pattern
  recorded in `ALPHAVAR_NAMING.md` (`alphavar.<domain>`). The legacy `options_lib` /
  `options_etl` are the seed of this domain package, just named by the narrow concretes;
  they fold into `alphavar.options` (logic) and `alphavar.options.etl`.
- The three-layer separation (R1) holds **inside each domain**: facade → pure logic →
  data (via injected provider from `io/`).

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

### R2.1 Uniform exchange interface — internal identity in, venue symbol stays inside

The public provider/exchange API speaks the library's **internal identity**, never the
venue's. Every method takes `asset_code` (+ typed scope: expiration, strike, type,
`RequestParameters`) — **not** an exchange `exch_symbol`. All exchanges are therefore
called **identically**; swapping Deribit for MOEX changes no call site.

- Building the venue request symbol from `asset_code` (and scope) is the **exchange
  class's** responsibility, done internally. The transform `asset_code → exch_symbol`
  (e.g. `BTC` + 30APR25 + 100000 + C → `BTC-30APR25-100000-C`) lives in the concrete
  exchange, nowhere else.
- On the way back, the exchange parses the venue response into the canonical columns
  (R4.1.1) — `asset_code` plus typed fields — and may keep `exch_symbol` as the optional
  raw audit column. Callers never see or pass a venue symbol.
- No public provider/exchange method accepts a `symbol`/`exch_symbol` parameter. (After
  T1b they take `asset_code`; this requirement keeps it that way.)

### R2.2 Project enums are separate from exchange API parameters

A project enum value (its `.value`/`.code`) is the **internal** name of a concept; it is
**not** automatically the string an exchange API expects. Never send a project enum
value straight onto the wire — map it explicitly per exchange.

- Each exchange owns an explicit **project-enum → API-string** mapping (e.g.
  `_DERIBIT_API_KIND[DeribitAssetKind] -> 'option' | 'future' | …`), used when building a
  request. The wire spelling lives only in that mapping, in the exchange module.
- Rationale (real bug, 2026-06-14): `DeribitAssetKind.OPTION.value` was `'options'`
  (inherited from `AssetKind.OPTIONS.value`) and was sent as the Deribit `kind=` param,
  but Deribit wants singular `'option'` → HTTP 400, so **Deribit option snapshots
  silently failed**. The fix was an explicit API-kind map, decoupling the internal enum
  from the venue's wire format.
- Symmetric to R2.1 (identity) and R4.5 (internal classification values): internal names
  stay internal; the exchange layer translates at the boundary, both directions.

Rationale: a venue symbol is an exchange-specific encoding; leaking it into the shared
API would couple callers to one venue's format and break the "new data source =
new provider, no caller changes" rule.

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

### R4.1.1 Instrument identification: two-level model

Two distinct identity concepts, deliberately different columns (the legacy `symbol`
naming conflated them):

| Concept | Column | Examples | Role |
|---|---|---|---|
| Underlying asset | `ASSET_CODE` (`asset_code`) | `BRN`, `BTC`, `AAPL` | The base asset a contract is written on. The **unifying key**: a future and an option on BRN share it. Short, stable; suitable for file/dir names. Present for every row. The library's own identity — exchange-neutral. |
| Exchange instrument symbol | `EXCH_SYMBOL` (`exch_symbol`) | `BTC-30APR25-100000-C`, `BR-3.25`, `AAPL` | The venue's raw contract identifier (exchange-facing ticker). Encodes expiry/strike/right in a string. Prefixed `exch_` like all other raw venue data (R4.2). |

This matches industry usage: *symbol/ticker* = exchange-facing instrument code;
*asset* = the underlying. So `asset_code` ≠ `exch_symbol` — separate columns, not
synonyms. (For a spot asset like `AAPL` the two coincide.) The legacy `symbol` /
`exchange_symbol` naming is replaced by `exch_symbol` (and `asset_code` for the
underlying).

**`exch_symbol` is not part of the canonical parsed dataset.** Once a book is
normalized, the contract is fully and compactly identified by typed columns
`(asset_code, expiration_date, strike, option_type, timestamp)`. The raw `exch_symbol`
string is then redundant and storage-expensive (a string per row). Keep it only:
- in **raw book snapshots** (it is what the exchange sent; the source for parsing/debug);
- as an **optional** audit column in parsed data, behind an ETL flag (like
  `source_fields`) — never a required column.

The mandatory row key for parsed options is
`(asset_code, expiration_date, strike, option_type, timestamp)`; for futures
`(asset_code, expiration_date, timestamp)`. `base_code`/`underlying_code` remain their
own concepts (sub-asset / underlying contract), distinct from `asset_code`.

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
(`exhchange_…`) and conflated layers. Migration is covered by the backlog (T23.6).

### R4.3 Single entity registry — one name per concept, everywhere

There is **one** registry of entity names (the column dictionary, `Col` in
`core/dictionary/`). A concept has exactly one canonical name there, and that name is
**the only** spelling used for it across the whole codebase — not just DataFrame
columns:

1. **DataFrame columns** — referenced only via the registry (`Col.STRIKE`), never as a
   string literal. (Existing R4 rule, now part of the registry contract.)
2. **Variables, parameters, attributes** — a variable holding one concept is named after
   its registry key: `asset_code` (not `symbol`/`code`/`ac`), `exch_symbol`,
   `expiration_date`. A collection is the plural (`asset_codes`). The function
   parameter that receives a strike is `strike`, etc.
3. **Function names that act on / produce a column** — encode the registry name of the
   column they read or write:
   - producing column `X` → `add_<x>` / `get_<x>` / `calc_<x>` (e.g. `add_intrinsic_value`
     produces `Col.INTRINSIC_VALUE`; `get_price_status` returns `Col.PRICE_STATUS`).
   - the verb says the effect (`add_` mutates/returns the frame with the column, `get_`
     returns the series/value, `calc_` is the pure computation), the noun is the exact
     registry name.
   - a function keyed to a concept must not drift from the column name (no
     `add_timevalue` for `Col.TIMED_VALUE`).

**Why:** the same concept must be greppable and unambiguous from column to variable to
function to file. If `Col.TIMED_VALUE = "timed_value"`, then the column, the local var,
the param, and `add_timed_value` all read `timed_value`. This is what makes the rename
discipline (asset_code, exch_symbol, exch_mark_price, …) enforceable and what lets the
pandera schema layer (R4.4) bind to the registry by reference, not by repetition.

The registry is **engine-neutral** (plain strings; no pandas/polars types in it — R8)
and **layered** (core base names + per-domain extensions, R0/R4 "core + domain
extensions"): generic concepts (`timestamp`, `price`, `iv`, `asset_code`, greeks) live
in `core`; domain concepts (`strike`, `option_type`, `price_status`) live in the
domain's dictionary and extend core.

### R4.4 Schemas bind to the registry, never restate names

DataFrame schemas (pandera `DataFrameModel`s) are the validation + dataset-composition
layer. Every schema field binds to a registry name **by reference**
(`pa.Field(alias=Col.STRIKE)`), never by retyping the string. Shared column groups
(timestamp / quote / OHLC / greeks) are **mixin** models; entity models
(`OptionsHistory`, `FuturesHistory`, `SpotHistory`, `OptionsBook`) compose mixins +
domain fields. Validation runs at layer boundaries (provider/exchange normalize output;
enrichment in dev) with `strict=False`, `coerce=True`, `lazy=True`; disabled in
production ETL via config. See the backlog (T23) for the build-out.

### R4.5 Classification axes — one word per axis

An instrument is classified along several **independent axes**. Each axis is a distinct
column and a distinct enum, and each classifier word (`kind`, `class`, `right`, `style`,
`tenor`) is reserved for exactly one axis — never reused. The legacy `type` was
overloaded (held a *kind* in `asset_type`, a *class* in `underlying_asset_type`, a
*right* in `option_type`); it is retired in favor of these:

| Axis | Column | Enum | Stored values | Where it lives | Notes |
|---|---|---|---|---|---|
| Instrument kind | `instrument_kind` | `InstrumentKind` | `option` / `future` / `spot` (**singular**) | per-row column (`core`) | the *form* of instrument. Singular — one row is one contract, matching exchange APIs (Deribit `kind="option"`). Was `asset_type` (mislabeled) with plural values. |
| Asset class | `asset_class` | `AssetClass` | `equity` / `commodity` / `crypto` / `index` / `currency` | property of `asset_code` (`core`) | nature of the *underlying*. Was the `AssetType` enum. |
| Contract kind | `contract_kind` | `ContractKind` | `vanilla` / `cso` / `stir` / `combo` … | per-row column (`core`) | same asset class, different product. Deribit `*_combo` → here. |
| Option right | `option_right` | `OptionRight` | `call` / `put` | per-row column (`options` domain) | the *right* (call=buy, put=sell). **Not** `side` (side = buy/sell of a position, a different concept reserved for legs). Was `option_type`. |
| Option style | `option_style` | `OptionStyle` | `american` / `european` | reference property of the instrument (`options` domain) | changes the pricing model. |
| Series tenor | `series_tenor` | `SeriesTenor` | `weekly` / `monthly` / `quarterly` | series property (`options` domain) | separate trading series on one asset class. Lower priority. |

Rules:
- **Stored values describing one row are singular**, following the domain's name for a
  *single contract* (`instrument_kind="option"`, not `"options"`) — this overrides any
  notation preference and matches exchange APIs. This is the data-value counterpart of
  R4.1: package/class names for the *domain/collection* stay plural (`alphavar.options`,
  `OptionsColumns`), but a value in a per-row column names *one* instrument, so singular.
  **Migration:** today `AssetKind` stores plural (`"options"`/`"futures"`) in parquet and
  in the dir layout (`DERIBIT/BTC/options/…`); moving to singular requires a parquet +
  path migration (backlog T23.6 / data migration).
- **Columns are singular** (one row = one instrument's attribute): `option_right`,
  `instrument_kind`, `option_style`. **Enums are singular** too (`OptionRight` — one
  value out of a set, like `enum Color`), an intentional exception to R4.1's "plural for
  classes": a value-enum names a single value, whereas `OptionsColumns` names a
  *collection* of columns.
- Identity vs classification: *what* the contract is on = `asset_code` (R4.1.1); *how*
  it is classified = these axes. Don't encode an axis into `asset_code`.
- `instrument_kind`/`asset_class`/`contract_kind` are domain-neutral → `core`;
  `option_right`/`option_style`/`series_tenor` are options-domain → `alphavar.options`.

**Axis enums are plain `StrEnum`; storage compactness is the schema's `category` dtype,
not a hand-rolled code.** The legacy `EnumCode` (value `"option"` + short code `"o"`,
storing `"o"` in parquet) is retired: a `StrEnum` member *is* its readable value
(`df[Col.OPTION_RIGHT] == OptionRight.CALL` needs no `.code`/`.value`), and the
pandas/polars `category` dtype — declared in the pandera schema (R4.4) — gives the same
memory/filter win automatically while keeping raw data readable (`"call"`, not `"c"`).
So: human values in data, no manual codes, `category` dtype for the categorical columns.
Migration: existing parquet stores the old short codes (`"o"`, `"c"`) and must be
expanded to values (backlog data migration).

### R4.6 Reference data vs time series — normalize, don't denormalize per row

Quote/history DataFrames hold **only time-varying, per-row data**. Attributes that are
constant for a whole instrument (or asset, or currency) are **not** stored as a repeated
column on every row — they live in separate **reference entities**, loaded and passed as
objects, never broadcast into the frame. Rationale (measured on a real Deribit options
file): constant string columns `kind`/`symbol`/`option_type` alone were ~8.8 MB of ~25 MB
(~35%) — pure repetition.

**What goes where:**
- **Per-row (stays in the quotes frame):** anything that varies row to row —
  `option_right` (call *and* put exist per strike), `strike`, `expiration_date`,
  `price`, `iv`, `ask`, `bid`, `volume`, `timestamp`, greeks, the `exch_*` raw values.
- **Contract-level reference** (one record per `(asset_code, expiration_date, strike,
  option_right)` — verified 1:1 with `exch_symbol`): `exch_symbol`, `option_style`,
  `contract_size`, tick size, lot size.
- **Asset-level reference** (one record per `asset_code`): `instrument_kind`,
  `asset_class`, `currency`, base/underlying codes, multiplier.
- **Class/currency-level reference** (shared across many instruments): interest `rates`
  per currency; `splits`/`dividends` per equity `asset_code`. These are their own
  reference entities, not attached to one instrument.

**Two design rules:**
1. **Temporal validity (slowly-changing dimension).** Reference data changes over time
   (`contract_size` revisions, listing/delisting, dividend schedule). Reference records
   are **snapshots with a validity range** (`valid_from`/`valid_to`), not a single
   current row. A load for a date selects the snapshot valid then.
2. **Stored as an entity, not columns.** Reference data is persisted **separately** from
   quotes — `metadata`/reference parquet under the instrument's data folder (e.g.
   `{EXCHANGE}/{asset_code}/_meta.parquet`, class/currency references at the exchange or
   asset root), written/updated by ETL. On load it is read into a Pydantic entity
   (`InstrumentMeta`, `AssetMeta`, `RatesTable`, …) carried by `OptionData`/the facade —
   **never** merged back as constant columns. Analytics that need an attribute read it
   from the entity (or the library joins on demand for a specific computation).

This keeps quote files small and makes "what is true about this instrument over time" a
first-class, queryable thing rather than redundant column noise.

## R5. Packaging

- Single distributable package: `alphavar`, rooted at `src/alphavar/` (uv + hatchling,
  `[tool.hatch.build.targets.wheel] packages = ["src/alphavar"]`). No second top-level
  package may live under `src/`.
- Every `import` used by shipped code must be a declared dependency (direct, not
  transitive). Subpackages shipped in the wheel that need optional dependencies
  (e.g. `options/etl` → `apscheduler`) must map to a pip **extra**, and their imports
  must fail with an actionable error message.

## R6. ETL isolation

- ETL (`alphavar/options/etl/`) consumes exchanges through the same
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

---

> Quality gates and the mandatory owner-verification rule (formerly R9/R10) now live in
> the development document — see [DEVELOPMENT_REQUIREMENTS.md](DEVELOPMENT_REQUIREMENTS.md)
> **D1** (quality gates) and **D2** (owner verification of math / DataFrame / architecture).
> Architectural changes to R0…R8 are themselves subject to D2 (explain + owner approval).
