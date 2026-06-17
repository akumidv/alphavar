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
- **Remaining:** data/parquet fixtures (DATA_PATH) for non-exchange tests
  (`exchange_provider_factory::test_get_provider_local`, chain/option/etl_history/
  timeframe_resample); xfail pending-logic tests (T19 chain load) per D1; full green run.

### T14b. Verify `chain_payoff` `RISK_PNL_PREMIUM` math (owner, D2)
`_calc_premium_profile` implemented (was `NotImplementedError`) as a symmetric
mark-to-market profile: `RISK_PNL` = expiration payoff, `RISK_PNL_PREMIUM` = per-strike
current P&L (intrinsic shift + current price − premium, capped at premium at risk; short
side mirrored). All 30 `risk_payoff_test` pass. **The math is NOT yet owner-verified** —
code marked `К ПРОВЕРКЕ`, original preserved commented in `payoff.py`. Not "Done" until
verified.

### T11a. Verify Deribit `kind` API param mapping (owner, D2)
`DeribitAssetKind.OPTION.value == 'options'` was sent as Deribit `kind=` → HTTP 400
(Deribit wants singular `'option'`); **option book snapshots silently failed in
production.** Fix: explicit `_DERIBIT_API_KIND` mapping (project enum → venue wire string)
in `deribit.py`, marked `# К ПРОВЕРКЕ`. Codifies R2.2 (project enums ≠ API params).
**Owner must verify** the mapping + that no other exchange sends a raw enum on the wire
(audit MOEX). Not "Done" until verified.

### T15. Add CI
No workflows exist (`.github/` has only `copilot-instructions.md`). Add a GitHub Actions
workflow: `poetry install --with etl,dev,test`, `pytest`, `pylint src/` on PR and push to
`main`. Depends on T11 for a green baseline.

---

## Block B — finish the core (T23 integration)

### T23.1. Migrate `OCl.X.nm` → `Col.X`; delete old column enums
Mechanical (sed-able) migration across existing code; **~24 src files still reference
`.nm`**. Delete `OptionsColumns`/`FuturesColumns`/`SpotColumns` enums once no usages
remain. Keep the typo string `"exhchange_mark_price"` as the value until T23.6 (data
compat). Do T23.7/T23.9 identifier renames alongside this.

### T23.3. Move dtype/resample metadata out of the dictionary
New `Col` registry already carries no dtypes (they live in pandera schemas). `resample_func`
still rides the old enum — move it to a `dict[str, str]` next to
`normalization/timeframe_resample.py` when the old enum is removed (blocked on T23.1).
Also fix `DataEngine.POLARIS` typo (overlaps T24).

### T23.4 (tail). Derive provider default column lists from models
Schema mixins + entity models exist (`options/schemas/`). Remaining: derive provider
default column lists from the models instead of hand-kept tuples (after T23.1).

### T23.5 (tail). Wire boundary validation
`options/schemas.validate(model, df)` + `ALPHAVAR_VALIDATE` toggle exist and are tested.
Remaining: call `validate(...)` at the actual ETL/exchange normalize boundary — blocked on
T23.6 (ETL still emits old column names; validating new schema against old names fails on
legit data). Wire in as part of T23.6.

### T23.6. Adopt the price/IV column model (R4.2)
Semantic flip: `PRICE`/`IV` become **our** normalized output (BS + smile fit + no-arb), not
exchange data; the venue's real values get an `exch_` prefix; no `fair_*` pair.
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
Rename `BookData.option`/`.future` → `.options`/`.futures`
(`io/exchange/_abstract_exchange.py`) and the `option = []` accumulator in
`io/exchange/moex.py`. Audit that no bare singular
`option`/`future` denotes a single entity (`option_type` etc. stay singular). Mechanical;
do alongside T23.1.

### T23.8. Pluralize facade class names (R4.1)
Public API change (one commit, update imports + tests + docs):
`OptionData`→`OptionsData`, `OptionChain`→`OptionsChain`, `OptionEnrichment`→
`OptionsEnrichment`, `OptionAnalytic`→`OptionsAnalytic` (and the Price/Risk variants).
Keep `Option` singular (single-instrument entry point); `option_class.py`/
`option_data_class.py` keep their file names.

### T23.9. Finish `symbol` → `asset_code` / `exch_symbol` split (R4.1.1, R2.1)
~44 `symbol` identifiers remain (28 in `etl_updates_to_history.py`, 9 in `deribit.py`, plus
provider/timeframe/facade). Two-level model (not a blind replace):
- Underlying asset code → `asset_code` (`option_symbol`, loop vars, `load_*` callers).
- Exchange instrument code → `exch_symbol` (`exchange_symbol`, `by_exchange_symbol`, …) —
  raw venue ticker, a different concept; do not fold into `asset_code`.
- Collections: `symbols`/`year_symbols`/`get_symbols_*` → `asset_codes`/`get_asset_codes_*`.
- **Column rename (R4.1.1):** `ASSET_CODE` currently wrongly holds the contract id
  (`deribit.py:259` maps `instrument_name`→`ASSET_CODE`). Split: venue contract string →
  new `exch_symbol` column; `asset_code` holds the underlying. Needs a parquet migration.
- **R2.1 audit:** no public provider/exchange method takes a `symbol`/`exch_symbol` param
  (T1b moved them to `asset_code`; add a regression guard). The `asset_code → exch_symbol`
  request transform lives inside each exchange class, not at call sites.
Identifier renames alongside T23.1; column split + R2.1 audit as part of T23.6 migration.

### T25. Reference data vs time series — normalize out instrument metadata (R4.6)
Quote frames repeat per-instrument constants every row (~35% of a real Deribit options
file). Split per-row data from reference entities; pass reference as objects, never
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
`io/exchange/cache.py` has serious concurrency flaws: `_lock()` ignores acquisition timeout
(proceeds unlocked after 1 s), `_unlock()` can release another thread's lock, bare
`except:` everywhere, `sys.getsizeof(df)` mis-measures DataFrame memory (use
`df.memory_usage(deep=True).sum()`), a DataFrame used as a concurrent metadata index.
`cachetools` is already declared — use `TTLCache` + a plain `threading.Lock`, drop
`psutil`.

### T13. Introduce `logging` instead of `print`
ETL, exchanges and messengers log via `print(..., file=sys.stderr)` (~8 src files). Add a
module-level `logging` logger; keep messenger notifications separate from diagnostics.

### T14. Clean up `option_data_class.py` and silent data mutation
Remove the 4× duplicated imports (lines 4-21). Reconsider the silent `dropna(subset=[PRICE])`
inside the `df_hist` getter — make it explicit (parameter or documented enrichment step).

### T16. Sync documentation with the post-rename layout
**Done (2026-06-17):** synced to the R0 restructure (`io/`, `options/` by layer/function) —
`AGENTS.md` source map; R0/R1/R2/R4 in `ARCHITECTURE_REQUIREMENTS.md`; `PROJECT_OVERVIEW.md`
(repo map, layer diagram, facade/dictionary/provider paths, deps, tests, extension table,
quick start; absent `pricer`/`forecast`/`validation` marked planned per R3/T21); the
`agents/shared/knowledge` + `agents/_dev/tools`/`skills` code pointers (`alphavar.io.*`,
`options/lib/*`). Repo-wide scan clean (only dated TASKS.md history retains old paths).

### T17. Repository hygiene
- Delete the untracked AI-chat artifact `options_pricing_backend.py` at the repo root
  (still present).
- (`old/` legacy tree already removed.)
- Remove any committed `__pycache__` artifacts if remaining.

### T18. Exception semantics in parsers
`DeribitMarket._kind_enrichment` raises builtin `SyntaxError` for data parse failures and
wraps it in a no-op `try/except ... raise err`. Introduce a dedicated `InstrumentParseError`
(in `exchange/exchange_exception.py`) and remove the dead re-raise.

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
Preparatory steps while still on pandas:
- Fix `DataEngine.POLARIS = "polaris"` → `POLARS = "polars"`
  (`io/provider/_provider_entities.py`).
- Remove engine-specific types from the dictionary's public contract (move dtype mapping to
  the per-engine schema layer from T23).
- Audit `options/lib` for hard-to-port idioms (row-wise `apply`, index reliance,
  `inplace=True`) — overlaps T20.

---

## P3 — later

### T21. Fill the planned facade components
`pricer`, `forecast`, `validation` are planned but absent. When implemented they must
follow R3 (a facade component class `options/<name>_class.py` over the shared `OptionData`,
with pure math in `options/lib`).

### T22. Windows portability of ETL
`EtlOptions.HOST_NAME = os.uname()[1]` fails on Windows — use `platform.node()`.
