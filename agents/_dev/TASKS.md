# Remediation Tasks — alphavar

> Backlog produced by the architecture/security review (2026-06-13), consolidated to the
> open remainder on 2026-06-17. Ordered by priority. Architecture/domain constraints:
> [ARCHITECTURE_REQUIREMENTS.md](../../docs/dev/ARCHITECTURE_REQUIREMENTS.md) (R0…R8, on new
> entities / domain changes). Day-to-day dev rules:
> [DEVELOPMENT_REQUIREMENTS.md](../../docs/dev/DEVELOPMENT_REQUIREMENTS.md) (D1…D4).
> Verification for every task: `pytest` + `pylint src/` green, plus **D2 owner
> verification** for any math/DataFrame/architecture change.

## Closed (archive)

**P0 — broken functionality:** T1, T1b, T2, T3, T4, T5, T6, T6b (2026-06-13).
**P1 — security:** T7, T8, T8b, T9, T10 (2026-06-13).
**T23 foundation (2026-06-13):** `core/dictionary` (`Col` plain-str registry) +
`options/dictionary` (`OptionsCol`, classification `StrEnum` axes), pandera schemas
(mixins + entity models, `category` dtype), parquet migration (`core/migration`,
`dictionary_v2` CLI). **Not yet integrated** — the legacy v1 column enums still run in
parallel (now under `options/dictionary`); production code not migrated to the registry.

Full historical detail for the closed items lives in git history of this file.

## Status & next priorities (2026-06-17)

Suite went 54 → 157+ passing during P0/P1. ~22 tasks remain.

**Critical path:** Block A (`T11` → `T14b`/`T11a` owner-verify → `T15`) gives a green,
guarded baseline; then Block B integrates the T23 registry; Block C parallelizes anytime.

1. **Block A — green baseline + CI:** **T11** (finish hermetic suite) → **T14b** + **T11a**
   (owner D2 verification) → **T15** (CI). Unblocks safe refactors and guards regressions.
2. **Block B — finish the core (T23):** integrate the registry (`OCl.X.nm`→`Col.X`, drop
   old enums), T23.6 (price/IV model), T23.7/8/9 (naming), **T25** (reference data /
   metadata). On the green baseline.

**Done — R0 package restructure (2026-06-17):** `provider`/`exchange`/`messanger` →
`alphavar.io`; `options_lib`+`options_etl`+root facade merged into `alphavar.options`,
laid out by layer then function (facade `*_class.py` at root; `dictionary`/`entities`/
`schemas` foundation; `lib/` pure logic; `etl/`). Tests mirror the new tree. R0/R1/R2/R4
in ARCHITECTURE_REQUIREMENTS + the AGENTS.md source map updated; D1 gains an
absolute-imports-only rule. pytest/pylint unchanged from baseline. **Remaining doc sync:**
`docs/dev/PROJECT_OVERVIEW.md` still describes the old tree (T16).
3. **Block C — independent improvements:** T12, T13, T14, T16, T17, T18, T19, T20, T24.
   Any time.

---

## Block A — green baseline + CI

### T11. Make the test suite hermetic and green
Mock HTTP, commit/generate small parquet fixtures, gate integration tests behind `-m
integration`.
**In progress (2026-06-14):**
- **Exchange network eliminated.** Recorded real Deribit+MOEX responses, replayed via
  `httpx.MockTransport`. Tooling: `agents/_dev/tools/exchange_fixtures/` (recorder) +
  `tests/utils/exchange_fixtures/{trim,mock}.py`; fixtures under
  `tests/unit/io/exchange/fixtures/<exch>/` (keyed by path+query, stores HTTP status,
  trimmed ~40–50 kB/exch). Exchange suite 100+s → ~1.8s. Heavy multi-asset walks marked
  `@pytest.mark.integration`; default run is `-m 'not integration'`.
- **Root-caused the DATA_PATH failures (2026-06-17):** the 49 errors + 1 failure were **not**
  missing data — `test.env` hard-coded a foreign absolute `DATA_PATH=/home/claude/…/data`
  that doesn't exist here. `conftest` already defaults to repo-relative `./data` when the env
  var is unset. Unsetting the override → **full suite green: 191 passed, 0 failed, 0 errors**
  (6 xfailed = T19, 6 integration deselected). This also gives real test coverage to the
  T23.1 resample model, T14b payoff, and T12 cache (they were only erroring on DATA_PATH).
- **Committed hermetic fixtures (2026-06-17):** added `tests/fixtures/data/` (~1.4 MB,
  trimmed: option EOD last 3 days, future EOD, 32 update snapshots) + the generator
  `tools/build_ci_fixtures.py`. `conftest` now defaults `DATA_PATH` to this committed set, so
  **a clean checkout is green with no local data** (191 passed; full local `./data` still
  usable via the `DATA_PATH` override). Added committed `test.env.example`.
- **Status:** suite hermetic + green. **Only T15 (the CI workflow) remains** to wire
  `pytest`/`pylint` on PR/push. xfail pending-logic tests (T19) already marked.

### T14b. Verify `chain_payoff` `RISK_PNL_PREMIUM` math (owner, D2)
`_calc_premium_profile` implemented (was `NotImplementedError`) as a symmetric
mark-to-market profile: `RISK_PNL` = expiration payoff, `RISK_PNL_PREMIUM` = per-strike
current P&L (intrinsic shift + current price − premium, capped at premium at risk; short
side mirrored). All 30 `risk_payoff_test` pass. **The math is NOT yet owner-verified** —
code marked `4VERIFY`, original preserved commented in `payoff.py`. Not "Done" until
verified.

### T11a. Verify Deribit `kind` API param mapping (owner, D2 — Type B, ⏳ ready)
`DeribitAssetKind.OPTION.value == 'options'` was sent as Deribit `kind=` → HTTP 400
(Deribit wants singular `'option'`); **option book snapshots silently failed in
production.** Fix (current): `DeribitAssetKind` is a venue-native enum whose `.value` IS the
singular wire token (`option`/`future`), decoupled from `InstrumentKind` (R2.2).
**Pinned** by `instrument_kind_mapping_test::test_deribit_asset_kind_values_are_venue_native`.
**MOEX audit done (2026-06-18): clean** — MOEX sends `MoexAssetType.value` (venue-native) on
the wire; project enums are used only to normalize responses. Tracked in the
[D2 ledger](../../docs/dev/D2_VERIFICATION.md); awaiting owner sign-off.

### T15. Add CI
**Done (2026-06-17):** `.github/workflows/ci.yml` runs on PR + push to `main`:
`astral-sh/setup-uv` (Python 3.14) → `uv sync --extra etl` → `uv run ruff check src tests
tools` → `uv run pytest` (hermetic on the committed `tests/fixtures/data`, T11). **Lint
migrated pylint → ruff** (owner request): replaced the dep + `[tool.pylint.*]` config with
`[tool.ruff]` (F/E/W/I/UP/B). Ran `ruff format` (116 files; double quotes, line wrapping,
trailing commas). Removed the giant inline API-response dumps from deribit/moex docstrings +
the bare table-string blocks in `deribit_market_test` (fixtures cover them now) and tidied a
few long comments → **E501 enabled** (line length 120); the only exception is
`payoff.py` (per-file ignore — its long lines are in the D2-preserved commented block, T14b). `ruff --fix` applied (imports sorted, typing modernized, unused removed);
fixed a latent circular import (`_timeframe_types` imported `EnumMultiplier` from the
package — now from the module) surfaced by import-sorting, plus B904/B905/B007/E721/F841.
ruff + pytest green; docs (D1, AGENTS, PROJECT_OVERVIEW) point at ruff.

---

## Block B — finish the core (T23 integration)

### T23.1. Migrate `OCl.X.nm` → `OptionsCol.X`; delete old column enums
**Pending owner verification (2026-06-17, D2):** migrated all `.nm`/`.value` column
references to the plain-string `OptionsCol` registry and **deleted**
`OptionsColumns`/`FuturesColumns`/`SpotColumns` + `_dataframe_columns.py`. The values are
preserved (already corrected: `exch_mark_price`/`exch_timestamp`/`option_right`), so the
swap is value-preserving. Added `OptionsCol.SERIES_CODE`; dropped unused `mark_price`/
`mark_iv`. Dataset membership moved to `_column_sets.py` (`OPTIONS/FUTURES/SPOT_COLUMN_
NAMES` + `OPTION_NON_*`/`ALL_COLUMN_NAMES` as `tuple[str,…]`). `enrichment_class` redesigned
to plain strings (no enum coercion/`isinstance`). `enum_code.py` kept (still used by
`RiskColumns`/`PriceColumns`). pytest unchanged from baseline (−2 obsolete enum tests
deleted); pylint clean of new errors. **4VERIFY:** the `_column_sets` membership and the
`DEFAULT_RESAMPLE_MODEL` reproduce the prior Futures/Spot enums + per-column `resample_func`
1:1 — owner to confirm (not test-covered: those tests error on DATA_PATH, T11). T23.7/T23.9
identifier renames still pending.

### T23.3. Move dtype/resample metadata out of the dictionary
**Mostly done (2026-06-17):** dtypes live in the pandera schemas (registry carries none);
`resample_func` moved to an explicit `DEFAULT_RESAMPLE_MODEL: dict[str, str]` next to
`lib/normalization/timeframe_resample.py` (T23.1). **Remaining:** fix `DataEngine.POLARIS`
typo (overlaps T24).

### T23.4 (tail). Derive provider default column lists from models — won't do
**Decided keep-explicit (2026-06-18):** the pandera entity models describe the *full* valid
column set; `provider.options_columns`/`futures_columns` are a deliberately small **curated
load subset** (timestamp/strike/expiration/right/price/underlying). Deriving the subset from
the full model is a poor fit and would risk changing what loads — the explicit `OptionsCol`
list is clearer. (A `Model.column_names()` helper can be added later if a caller needs the
full set; the provider default stays explicit.)

### T23.5 (tail). Wire boundary validation — done (2026-06-18, 4VERIFY — D2 ledger, Type B)
`options/schemas.validate(model, df)` + `ALPHAVAR_VALIDATE` toggle. The earlier blocker was a
schema/reality mismatch, **not** the pricer: the greeks (`iv`, delta…) are already optional
(`float | None` → absent column skipped), so the only false failures were non-null constraints
that contradict the data. Fixed honestly: `QuoteMixin.price` → nullable (our model output may
be absent; the clean accessor drops it later), `GreeksMixin.iv` → nullable (pricer returns NaN
out-of-bracket), `FuturesHistory.expiration_date` → nullable (PERPETUAL futures are NaT).
Then wired `validate_book_data(book)` (new, in `etl_class`) into both ETLs'
`get_symbols_books_snapshot`, validating each kind (`OptionsHistory`/`FuturesHistory`/
`SpotHistory`) at the **exchange→storage** boundary; no-op under `ALPHAVAR_VALIDATE=0`. Tests:
`options/etl/validate_book_data_test` (valid passes, bad `option_right` raises, disabled
no-ops) + the committed fixtures + the live deribit/moex normalizer frames all validate.
pytest 220 / ruff green.

### T23.6. Adopt the price/IV column model (R4.2)
**In-memory scope done (2026-06-18, 4VERIFY — D2 ledger):** the registry already carried
`exch_price`/`exch_iv`/`settle_*`/`exch_mark_*`/`exch_symbol` (no `mark_*`/`fair_*`), and the
Deribit/MOEX normalizers already map `mark_price`/`theorprice`→`exch_mark_*`. Added now:
`AbstractExchange.SOURCE_PREFIX` (`source_<col>`) → `RAW_SUFFIX` (`<col>_raw`) on the write
path (deribit enrichment, both ETL `_drop_service_or_doublet_columns`,
`_update_resample_model_for_source`); a **read-shim** `core.migration.rename_legacy_columns`
(idempotent old→new name map incl. `source_*`→`*_raw`) applied on parquet load in
`PandasLocalFileProvider`. Tests: `core/migration/read_shim_test`. pytest 203 / ruff green.
**Tail (a) done (2026-06-18, 4VERIFY — D2 ledger, Type B):** `fill_option_price` now derives
the venue traded/quoted price into **`exch_price`** (was our `price`); Deribit adds
`EXCH_PRICE` to `COLUMNS_TO_CURRENCY` so it gets `exch_price_raw` (pre-conversion coin) +
the ×`estimated_delivery_price` USD conversion (the bespoke `price`-conversion block removed);
MOEX is RUB-native (no conversion). Our `price` is then mirrored from `exch_price` by the new
`source_interim_price` (**interim** until the smile-fit pricer — behavior-preserving: the same
representative venue price still lands in `price`). `exch_iv` left nullable (neither venue
exposes a traded IV; only mark IV → `exch_mark_iv`). Our `iv` is available on demand via
`Option.pricer.add_iv()` (T21). Verified on the Deribit fixture: `exch_price` 6/6,
`price==exch_price`, `price≠exch_price_raw`. pytest 216 / ruff green.
**Remaining:** (b) ~~T23.5 validate() wiring~~ **done** (see T23.5 — schemas relaxed to match
reality, `validate_book_data` wired at the ETL boundary). (c) the one-off stored-parquet
migration (existing `migrate_parquet_tree` tool, run separately).

Original spec — Semantic flip: `PRICE`/`IV` become **our** normalized output (BS + smile fit
+ no-arb), not exchange data; the venue's real values get an `exch_` prefix; no `fair_*` pair.
- `price`/`iv`: keep names, now the project's model output (pricer/normalizer writes them;
  raw exchange data must no longer land here directly).
- Add `exch_price`/`exch_iv` — venue traded/quoted price as received.
- Replace `exhchange_mark_price`/`exchange_mark_iv` → `exch_mark_price`/`exch_mark_iv`
  (Deribit `mark_price`, MOEX `theorprice`).
- Add `settle_price`/`settle_iv` (EOD-only, nullable intraday; no `exch_` prefix).
- Rename `original_timestamp` → `exch_timestamp` (venue's own ts: Deribit
  `creation_timestamp`, MOEX `updatetime`). `request_timestamp`/`timestamp` stay ours.
- Remove planned `mark_*`/`fair_*` entries (superseded).
- Repoint Deribit/MOEX normalizers + `COLUMNS_TO_CURRENCY`. Replace `source_` prefix
  (`SOURCE_PREFIX`) with a `_raw` **suffix** (pre-currency-conversion value of `<col>` is
  `<col>_raw`); update `AbstractExchange.SOURCE_PREFIX` + the one call site (`deribit.py:241`).
- Read-shim on parquet load (old → new names) + one-off migration for stored data
  (extend `core/migration`).
- **Caution:** today raw exchange price flows into `price` via `fill_option_price`. Until
  the pricer exists, source `price` explicitly from `exch_price` so it is never silently
  empty — decide the interim behavior.

### T23.7. Pluralize collection identifiers (R4.1)
**Done (2026-06-18):** `BookData` (`io/exchange/_abstract_exchange.py`) and `AssetBookData`
(`options/etl/etl_class.py`) fields `option`/`future` → `options`/`futures`; updated all
constructors (deribit/moex etl + tests) and the `_save_timeframe_book_update` `fabric`
string keys (kept in sync with the fields for `getattr`/`setattr`); renamed the `option = []`
accumulator in `moex.py`. `spot` (mass noun) and the `*_combo` fields are left singular.
Audit: no other bare singular `option`/`future` denotes a collection. pytest 201 passed,
ruff clean.

### T23.8. Pluralize facade class names (R4.1)
**Done (2026-06-18):** renamed `OptionData`→`OptionsData`, `OptionChain`→`OptionsChain`,
`OptionEnrichment`→`OptionsEnrichment`, `OptionAnalytic`→`OptionsAnalytic` (+ `…AnalyticPrice`/
`…AnalyticRisk`) across src + tests + `options/__init__` exports; updated R1/PROJECT_OVERVIEW/
AGENTS docs. `Option` (single-instrument entry point), `ChartClass`/`ChartPriceClass`, and the
`option_class.py`/`option_data_class.py` file names are unchanged. pytest 201 passed, ruff clean.

### T23.9. Finish `symbol` → `asset_code` / `exch_symbol` split (R4.1.1, R2.1)
**Part A — identifier renames done (2026-06-18):** facade `option_symbol`/`_option_symbol`
→ `asset_code`/`_asset_code`; the `symbol`/`symbols`/`year_symbols`/`max_symbols` locals +
the `EtlHistory(symbols=…)` param → `asset_code`/`asset_codes`/…; `get_symbols_asset_by_…`
→ `get_asset_codes_by_…`; deribit/moex `symbols_df` → `asset_codes_df`,
`exchange_asset_symbol_arr` → `exch_symbol_arr`; the venue concept `by_exchange_symbol`/
`resample_by_exchange_symbol`/`_resample_by_kind_type_or_exchange_symbol` → `…exch_symbol…`.
Left singular by design: `get_symbols_books_snapshot`/`join_symbols_kind_…` (not
underlying-code holders) and the legacy `"symbol"` key in `COLUMN_RENAMES`. **R2.1 audit
done — clean:** no public provider/exchange method takes a `symbol`/`exch_symbol` param.
pytest 203 / ruff green.

**Part B — column split, Deribit done (2026-06-18, 4VERIFY — D2 ledger):** discovery —
**no stored-parquet migration is needed**: the committed Deribit data is already in the
target schema (`asset_code`=underlying, `exch_symbol`=contract, no `base_asset_code`). The
real work was aligning the **live normalizer** to it. Done for Deribit: `_normalize_book`
maps `instrument_name` → `EXCH_SYMBOL` (was `ASSET_CODE`); `_kind_enrichment` parses
`EXCH_SYMBOL` and sets `ASSET_CODE`=underlying for all kinds (was `BASE_CODE`); `deribit_etl`
routes/groups by `ASSET_CODE` (was `BASE_CODE`); tests assert the new split. pytest 203 /
ruff green, validated against the recorded API fixtures.

**Part B — MOEX prep done (2026-06-18): book-summary now hermetic.** The MOEX split was
blocked because `get_options_assets_books_snapshot` (the multi-step series/underlyings/desk
join where `ASSET_CODE`/`BASE_CODE` are overloaded) was `@integration` (live-API only), so a
rename couldn't be validated. Fixed: repaired the post-T23.1 recorder
(`agents/_dev/tools/exchange_fixtures/moex.py`: `OptionsColumns`→`OptionsCol`), added a
book-summary drive to it, **recorded the SI fixtures** (all 8 series + desks), trimmed
(608 KB→68 KB), and dropped `@integration` from `test_get_options_assets_books_snapshot` — it
now replays via MockTransport. pytest 204 / ruff green.

**Part B — MOEX split done (2026-06-18, 4VERIFY — D2 ledger):** aligned MOEX to the canon
under the now-hermetic book-summary test. Rename maps: API `asset_code`(underlying) →
`ASSET_CODE` (was `BASE_CODE`); `secid`/futures `futures_code`(contract) → `EXCH_SYMBOL` (was
`ASSET_CODE`); option `futures_code`(underlying future) stays `UNDERLYING_CODE`. The
book-summary join: `BASE_CODE`→`ASSET_CODE`, and the underlying-future merge now keys on the
future's **contract** (`EXCH_SYMBOL`→`UNDERLYING_CODE`). `moex_etl` routes/groups by
`ASSET_CODE` (dropped the `BASE_CODE`/SPOT branch). Verified end-to-end on the SI fixtures:
`asset_code`=SI, `exch_symbol`=option contract, `underlying_code`=future contract, the
underlying merge populates. **`BASE_CODE` decision (resolved): eliminated** from the live
pipeline (both venues) — `timeframe_resample` multi-asset grouping now uses `ASSET_CODE`; the
registry/`_column_sets`/migration keep the `base_asset_code` name only for reading legacy
data. pytest 204 / ruff green.

### T25. Reference data vs time series — normalize out instrument metadata (R4.6)
**Increment 1 done (2026-06-18, 4VERIFY — D2 ledger): entities + lossless split.** New
`AssetMeta` entity (`options/entities/_reference.py`, asset-level constants per `asset_code`)
+ pure lib `options/lib/reference` — `split_reference(df) → (quotes, AssetMeta, contracts)`
and its exact inverse `apply_reference`. Asset-level columns (`asset_code`, `instrument_kind`,
`asset_class`, `currency`, `contract_kind`, `title`) collapse to one `AssetMeta`; contract-
level columns (`exch_symbol`, `option_style`, underlying link) deduplicate into a frame keyed
by `(expiration_date, strike, option_right)` — but **only the ones provably constant per key**
are moved (a feed's time-varying `underlying_expiration_date` correctly stays in the series),
so the split is always lossless. Measured on the BTC fixture: **−26% memory**, round-trip
exact. Tests: `options/lib/reference/split_test` (round-trip, extraction, dedup, reject
multi-asset / non-constant). pytest 225 / ruff green.

**Increment 2 done (2026-06-18, 4VERIFY — D2 ledger): SCD Type 2.** Added `Col.VALID_FROM`/
`VALID_TO` to the registry + pure `options/lib/reference._scd`: `as_of(history, when, keys)`
(select the version valid at a date: `valid_from` <= t < `valid_to`, NaT = open) and
`append_on_change(history, snapshot, when, keys, attrs)` (fold a new observation in — new key →
open record; changed attribute → close prior `valid_to`=when + open a new one; unchanged →
no-op; a key absent from the snapshot is left open, never auto-expired). Tests:
`options/lib/reference/scd_test` (6 cases incl. the exclusive-`valid_to` boundary), warning-
clean under `-W error::FutureWarning`. pytest 231 / ruff green.

**Increment 3 done (2026-06-18, 4VERIFY — D2 ledger): storage adapter.** Pure file-I/O
`options/lib/reference._store` over a per-asset directory: `write_reference(asset_dir, asset,
history)` / `read_reference(asset_dir) → (AssetMeta | None, history)`. The reference lives at
the asset root beside the time series — asset-level `AssetMeta` as `_asset.json` (sidecar),
contract-level SCD-2 history as `_meta.parquet`. An absent reference reads back as
`(None, empty frame)` so an SCD history starts fresh via `append_on_change`. Timestamps are
stored at millisecond resolution (parquet default; second-rounding is fine — the project's
minimum analysis timeframe; nanoseconds never needed). No provider coupling yet (increment 4). Tests: `options/lib/reference/store_test` (absent→fresh,
AssetMeta + tz-aware SCD round-trip, file placement, write→append→rewrite), warning-clean under
`-W error::FutureWarning`. pytest 235 / ruff green.

**Increment 4 Part A done (2026-06-18, 4VERIFY — D2 ledger): read-side facade wiring (additive).**
Provider now serves the reference: `AbstractProvider.load_reference(asset_code)` defaults to
`(None, empty)` (exchange/live providers have no stored reference); `AbstractFileProvider`
overrides it to `read_reference` over `{exchange}/{asset_code}/` (returns `(None, empty)` when no
`_meta.parquet`/`_asset.json` is present — i.e. today's pre-migration wide files). `OptionsData`
gained lazy `.reference` (`AssetMeta | None`) / `.reference_history` + `reapply_reference(df)`
(broadcasts asset-level constants onto a frame — idempotent, no-op when no reference is stored or
a column is already present); `Option.reference` exposes it on the facade. **Purely additive** —
the existing `df_hist`/`df_fut` load path is unchanged, so current behavior is byte-for-byte
preserved (reference is `None` until increment 5 migrates the stored files). Tests:
`io/provider/file_provider_test` (absent→None, round-trip), `options/option_data_class_test`
(absent no-op, broadcast, no-overwrite). pytest 240 / ruff green.

**Increment 5 done (2026-06-18, 4VERIFY — D2 ledger): migration extract — wide → reference
sidecars (extract-only, additive).** Pure `extract_reference(df, when) → (AssetMeta, contract
SCD-2 history)` in `options/lib/reference` (split the wide frame, seed one open contract version
at `when`; empty history for a contract-less/futures-only asset). Operational driver
`options/etl/reference_migration` (mirrors `legacy_parquet`: dry-run default / `--apply` / CLI
`python -m …reference_migration {exchange_dir}`): per asset, concat its options history, pick
`when = min(timestamp)`, write `_asset.json` + `_meta.parquet` beside the series.
**EXTRACT-ONLY** — the wide `{kind}/{timeframe}/{year}.parquet` series files are left
**unchanged** (slimming the series needs the contract-level as-of rejoin on load, deferred), so
this is purely additive: reads keep working, `Option.reference` (inc.4A) now resolves. Dry-run on
the committed BTC fixture: 838 contracts extracted, series untouched. Tests:
`options/lib/reference/migration_test` (asset-meta + one-open-version-per-contract, empty case,
sidecars-written + series-untouched, skip-no-options). pytest 244 / ruff green.

**Increment 4B done (2026-06-18, 4VERIFY — D2 ledger): ETL keeps the reference sidecar current
(additive).** `EtlHistory._fold_reference(asset_code, df)`, called right after each history
year-file write (gated by the new `update_reference=True` param), folds the options reference
into the asset's SCD-2 sidecar via `split_reference` → `append_on_change` (`when` = the batch's
latest observation): new contract → open version; changed attribute → close prior + open new;
unchanged → no-op. **Options-only** (skips frames without the contract key) and **additive** —
writes only `_meta.parquet`/`_asset.json`, never the series. **Guarded**: any reference failure
is logged, never aborts the history write. Tests: `options/etl/etl_reference_fold_test` (writes
sidecar, append-on-change, unchanged no-op, skip-non-options). pytest 248 / ruff green.

**Series slimming done (2026-06-18, 4VERIFY — D2 ledger): slim series + as-of rejoin on load
(opt-in; lossless).** Load side (always on, conditional): `join_reference_asof(quotes, history,
keys, time_col)` — interval as-of join attaching each row's contract reference valid at its own
timestamp (`valid_from` <= t < `valid_to`); `OptionsData._restore_reference` runs it + the
asset-level broadcast after load, **filling only absent columns** → slim and legacy-wide files
read identically (no-op on wide). Write side (opt-in `slim_series=False`, and only when
`update_reference` is on so the drop is reversible): `EtlHistory._to_stored_series` writes
`split_reference().quotes` (drops the reference columns now in the sidecar). **Keystone:** the
wide→slim+sidecar→load round-trip is lossless through the real `OptionsData` path
(`options/lib/reference/slim_roundtrip_test`). Tests: `scd_test` (as-of per-row time, unmatched
NaN, no-overwrite), `etl_reference_fold_test` (slim only when enabled, guard requires
update_reference). pytest 254 / ruff green. **Storage actually shrinks only once `slim_series` is
flipped on (owner decision); default keeps wide files + the now-populated sidecars.**

**Migration tooling consolidated (2026-06-18): convert accumulated data + updates.** Two
committed self-documenting CLIs — `alphavar.core.migration.legacy_parquet` (column conversion,
any parquet tree incl. updates) + `alphavar.options.etl.reference_migration` (reference meta
formation from history; now scans `option`/legacy-`options` folders) — tied together by the new
**`migrate-stored-data`** skill (`agents/_dev/skills/`), which orders the end-to-end conversion
(history + updates → column-convert; history → meta) and codifies that new legacy/edge cases are
encoded **in the tools + a pinning test**, never a throwaway script. Indexed in tools/skills READMEs.

**Data health tool (2026-06-19): `agents/_dev/tools/data_migration` (general verify+fix script).**
`verify {exchange_dir}` — fast read-only diagnosis of **metadata / structure / types** (legacy &
unknown columns vs the full registry vocabulary; datetime must be tz-aware, ns flagged per the
ms-convention; price/iv/greeks numeric; reference sidecar present + matches folder + covers every
contract key; slim-without-sidecar = error). `fix {exchange_dir} [--apply]` — runs column
conversion + reference meta, then re-verifies. Reuses the library code; the skill now drives this
tool. Tests: `tests/unit/agents/tools/data_migration_test` (clean, legacy+dtype, tz-naive,
slim-no-sidecar, sidecar-ok, exchange walk). pytest 260 / ruff green.

Original spec — Quote frames repeat per-instrument constants every row (~35% of a real Deribit
options file). Split per-row data from reference entities; pass reference as objects, never
broadcast as constant columns.
- **Layers:** asset-level (`instrument_kind`, `asset_class`, `currency`, multiplier) per
  `asset_code`; contract-level (`exch_symbol`, `option_style`, `contract_size`, tick/lot)
  per `(asset_code, expiration_date, strike, option_right)`; class/currency-level (`rates`,
  `splits`/`dividends`). `option_right` stays per-row (call+put coexist), NOT reference.
- **SCD:** reference records carry `valid_from`/`valid_to`; a load for a date selects the
  snapshot valid then; ETL appends on change instead of overwriting.
- **Storage:** separate parquet under the instrument folder
  (`{EXCHANGE}/{asset_code}/_meta.parquet`; class/currency refs at exchange/asset root).
  Not parquet schema-metadata.
- **Entities:** Pydantic (`InstrumentMeta`, `AssetMeta`, `RatesTable`, `CorporateActions`)
  carried by `OptionData`/facade; analytics read from the entity or lib joins on demand.
- Sequences on top of T23; update `core/migration` to extract metadata from existing wide
  parquet into the new reference files.

### Merge `options_lib` + `options_etl` → `alphavar.options` (R0)
**Done (2026-06-17):** folded `options_lib` (→ `options/lib` + `options/{dictionary,
entities}`) and `options_etl` (→ `options/etl`) plus the root facade into `alphavar.options`,
laid out by layer then function; `provider`/`exchange`/`messanger` → `alphavar.io`. Tests
mirror the new tree; docs (R0/R1/R2/R4, AGENTS.md, PROJECT_OVERVIEW) synced. The remaining
T23 work (registry adoption, drop the v1 enums) is independent of the physical layout.

---

## Block C — independent improvements

### T12. Replace the custom `Cache` with `cachetools`
**Done (2026-06-17, 4VERIFY for eviction semantics):** rewrote `io/exchange/cache.py` on
`cachetools.TTLCache(maxsize, ttl=30 min)` + a plain `threading.Lock` (get/set under the
lock, the wrapped call outside it). Dropped the hand-rolled cache entirely — the
timeout-ignoring `_lock`, cross-thread `_unlock`, bare `except:`, the `validate_df`
DataFrame-as-index, `sys.getsizeof`, and the `psutil` memory budget. `.it` decorator
semantics preserved (key from func name + non-`self` args/kwargs; returns a deep copy).
`psutil` removed from `[project.dependencies]` + `uv.lock` (was only used here). cache.py
pylint 10/10; pytest unchanged from baseline. **4VERIFY (D2):** eviction is now by item
count, not a memory budget — `Cache(128, …)` means 128 items (was 128 MB); cache is
transparent (miss = recompute), so this is capacity-only, not correctness.

(superseded detail) The old `io/exchange/cache.py` had serious concurrency flaws: `_lock()`
ignored acquisition timeout (proceeded unlocked after 1 s), `_unlock()` could release
another thread's lock, bare `except:` everywhere, `sys.getsizeof(df)` mis-measured (use
`df.memory_usage(deep=True).sum()`), a DataFrame used as a concurrent metadata index.
`cachetools` is already declared — use `TTLCache` + a plain `threading.Lock`, drop
`psutil`.

### T13. Introduce `logging` instead of `print`
**Done (2026-06-17):** added a module-level `logger = logging.getLogger(__name__)` and
converted diagnostic `print(...)` to `logger.{error,warning,info}` with lazy `%`-args (no
W1203) in `io/exchange/{deribit,moex,cache}.py`, `options/etl/{etl_class,
etl_updates_to_history}.py`, `lib/normalization/datetime_conversion.py`; dropped the now-unused
`import sys` (deribit, etl_class). **Kept as-is** (delivery/CLI, not diagnostics):
`io/messanger/stdandard.py` (`StandardMessanger` console delivery) and the
`core/migration/legacy_parquet.py` CLI prints; the ETL report still goes through
`messanger.send_message`. pytest/pylint unchanged from baseline.

### T14. Clean up `option_data_class.py` and silent data mutation
**Done (2026-06-18, 4VERIFY for the drop default):** the 4× duplicated imports were
removed by `ruff --fix` (T15). The silent `df_hist`-getter `dropna(subset=[PRICE],
inplace=True)` is now an explicit, overridable `OptionData(..., drop_na_price=True)` flag
(default preserves the prior behavior), documented in `__init__` and the getter (marked
`4VERIFY`); guarded on the column being present (was a `KeyError` for custom
`option_columns` without price). ruff + pytest green.

### T16. Sync documentation with the post-rename layout
**Done (2026-06-17):** synced to the R0 restructure (`io/`, `options/` by layer/function) —
`AGENTS.md` source map; R0/R1/R2/R4 in `ARCHITECTURE_REQUIREMENTS.md`; `PROJECT_OVERVIEW.md`
(repo map, layer diagram, facade/dictionary/provider paths, deps, tests, extension table,
quick start; absent `pricer`/`forecast`/`validation` marked planned per R3/T21); the
`agents/shared/knowledge` + `agents/_dev/tools`/`skills` code pointers (`alphavar.io.*`,
`options/lib/*`). Repo-wide scan clean (only dated TASKS.md history retains old paths).

### T17. Repository hygiene
**Done (2026-06-17):** removed the stray AI-chat artifact `options_pricing_backend.py`
from the repo root (was tracked, not untracked; a "Generated by claude" transcript,
referenced nowhere). `old/` legacy tree already gone; no committed `__pycache__` in git.

### T18. Exception semantics in parsers
**Done (2026-06-17):** added `InstrumentParseError(ValueError)` in
`io/exchange/exchange_exception.py`; `deribit._kind_enrichment` now raises it (4 sites,
was builtin `SyntaxError`) and the dead `try/except SyntaxError … raise err` wrapper is
removed (body de-indented). pytest/pylint unchanged. **Note:** the parse-error path is not
yet test-covered (no test asserted the old `SyntaxError`); a small `InstrumentParseError`
test would be worthwhile.

### T19. Finish or fence `PandasLocalFileProvider` period loading
**In progress (2026-06-14) — tests marked, implementation pending:**
- **`load_options_chain`:** owner contract is "load the chain from local history, else
  return `None`" — needs new logic (currently `NotImplementedError`). Dependent tests are
  `xfail(reason="pending T19 …")`: `chain_classs_test::{test_select_chain,
  test_getter_option_chain, test_get_settlement_and_expiration_date, test_get_desk}` and
  `option_class_test::test_chain_select_chain`. (`OptionChain.select_chain` already falls
  back to build-from-history when the provider returns `None`.)
- **`_load_data_for_period` (owner D2):** multi-year / date-range loading not implemented
  (needs owner-approved date semantics — `timestamp` is `pd.Timestamp`: date vs `.dt.date`,
  inclusive bounds, missing-year handling). Replace exact-`type()` matching with `isinstance`
  (check `datetime` before `date`). Fix the magic `"datetime"` literal → `OCl.TIMESTAMP.nm`
  (`timestamp`). Branches stay explicit `NotImplementedError` fences until verified.
- **T1 leftover:** `test_option_class_with_extra_columns` is xfailed — blocked on T23.6
  (committed data is pre-dictionary-v2: `exchange_price/iv` vs registry names), unrelated to
  T19.

### T20. Vectorize Deribit book normalization
`_normalize_book` applies `_kind_enrichment` row-by-row (`df.apply(axis='columns')` with a
deep copy per row) over ~5000 instruments per snapshot — the dominant ETL cost. Vectorize:
split `instrument_name` with `str.extract`/`str.split` once, derive kind/strike/expiration
by masks. Overlaps T24.

### T24. Polars readiness (R8)
- **Done (2026-06-17):** fixed `DataEngine.POLARIS = "polaris"` → `POLARS = "polars"`
  (`io/provider/_provider_entities.py` + the 3 `exchange_provider_factory` references).
- **Done (via T23):** the dictionary's public contract carries no engine-specific dtypes
  (the `Col`/`OptionsCol` registry is plain strings; dtypes live in the pandera schemas).
- **Remaining:** audit `options/lib` for hard-to-port idioms (row-wise `apply`, index
  reliance, `inplace=True`) — overlaps T20.

---

## P3 — later

### T21. Fill the planned facade components
**Pricer done (2026-06-18, 4VERIFY — D2 ledger, Type C):** `options/lib/pricer/` (pure
Black-76 forward model: `bs_forward_price`, `bs_vega`, `implied_vol` by bisection, `norm_cdf`;
+ `_enrich` df helpers `add_model_iv`/`add_fair_price`/`years_to_expiry`) + facade
`OptionsPricer(OptionsData)` wired into `Option.pricer` and exported. Forward `F` =
`underlying_price` (Deribit quotes on the future), `rate=0` default, ACT/365 tenor. 11 tests:
ATM reference (7.9656), put-call parity, round-trip IV (scalar + vectorized + df), degenerate
intrinsic, out-of-bracket NaN, vega. pytest 215 / ruff green. **This unblocks T23.5 / T23.6
tail** (an `iv` column is now computable). **Still planned:** `forecast`, `validation`
components; and the smile-fit / no-arb layer that would make `price` a true model output (vs
sourced from `exch_*`).

### T22. Windows portability of ETL
`EtlOptions.HOST_NAME = os.uname()[1]` fails on Windows — use `platform.node()`.
