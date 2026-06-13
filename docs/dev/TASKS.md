# Remediation Tasks — alphavar

> Backlog produced by the architecture/security review (2026-06-13). Ordered by
> priority. Architecture constraints for all tasks:
> [ARCHITECTURE_REQUIREMENTS.md](ARCHITECTURE_REQUIREMENTS.md).
> Verification for every task: `pytest` + `pylint src/` green.

## P0 — Broken functionality (fix first)

### T1. Fix Deribit book normalization crash
`src/alphavar/exchange/deribit.py:261` references `OptionsColumns.EXCHANGE_PRICE`,
which no longer exists (renamed to `EXCHANGE_MARK_PRICE` during refactoring). Every
Deribit book snapshot raises `AttributeError`; 10+ tests in
`tests/unit/exchange/deribit_market_test.py` fail. Audit the whole module (and
`moex.py`) for other stale enum names after the rename.
**Done (2026-06-13):** fixed `EXCHANGE_PRICE`→`EXCHANGE_MARK_PRICE` (deribit, moex,
etl_updates_to_history), removed dead `SETTLEMENT_IV` write, fixed `AssetType.OPTIONS/
FUTURES`→`AssetKind.*` (moex, moex_etl). Added an enum-validity scan; src is clean.

### T1b. Fix `AbstractProvider` ↔ exchange method-name mismatch
The "option→options"/"future→futures" rename touched `AbstractProvider`
(`load_options_history`, `load_options_book`, `load_options_chain`,
`load_futures_history`, `load_futures_book`, `get_asset_history_years`, all taking
`asset_code`) but **not** the exchange subclasses (`deribit.py`, `moex.py`,
`binance.py`), which still declare the old singular names with a `symbol` parameter.
Result: `DeribitExchange()`/`MoexExchange()`/`BinanceExchange()` cannot be instantiated
(`TypeError: Can't instantiate abstract class ... without an implementation for ...`),
breaking all ETL tests. Rename the methods/params to match the abstract contract.
**Done (2026-06-13):** renamed `load_option*`→`load_options*` / `load_future*`→
`load_futures*` and `symbol`→`asset_code` in deribit/moex/binance + the two callers in
`etl_updates_to_history.py`; added `get_asset_history_years` stub to all three
exchanges. All three now instantiate; ETL tests that don't depend on `DATA_PATH` pass.
Remaining `PermissionError`s are the stale absolute `DATA_PATH` (see T7/T11).

### T2. Fix `SaveTask` mutation bug in ETL save path
`SaveTask` is a `NamedTuple`, but `EtlOptions._save_task_dataframe()` ends with
`save_task.df = None` (`etl_class.py:347`) — raises `AttributeError` on every save.
Convert `SaveTask` to a `@dataclass` (it is mutated) or drop the mutation.

### T3. Remove duplicated `src/options_etl/` package
`src/options_etl/` is a diverged pre-rename copy of `src/alphavar/options_etl/` with
stale `from options_etl...` imports. It is not shipped in the wheel and silently drifts
from the real code. Delete it; keep only `src/alphavar/options_etl/`. Check `demo/`
scripts for imports of the old path.
**Done (2026-06-13):** `git rm -r src/options_etl`; repointed 4 demo scripts from
`from options_etl ...` to `from alphavar.options_etl ...`. No stale references remain.

### T4. Fix dead exception handling around thread pools
`executor.map()` raises on iteration — it never yields `Exception` objects, so:
- `EtlOptions._book_snapshot_timeframe_job` (`etl_class.py:241`): the
  `isinstance(book_data, Exception)` branch is dead; one failing asset aborts the whole
  job loop and remaining assets are lost for that timeframe tick.
- `DeribitExchange.get_options_assets_books_snapshot` (`deribit.py:367-371`):
  `job_res.result()` raises; the `isinstance(..., Exception)` check is dead code.
Use `submit()` + `as_completed()` with per-task `try/except`, log the failed asset,
continue with the rest.
**Done (2026-06-13):** ETL `_book_snapshot_timeframe_job` now uses
`submit()`+`as_completed()` with per-asset try/except + `continue` (one failing asset
no longer aborts the tick); `_save_tasks_dataframes_job` likewise surfaces save errors
instead of swallowing the lazy `map`. Deribit snapshot keeps fail-fast but via real
`try/except` around `.result()`. Removed dead `functools` import.

### T5. Move `EtlOptions` mutable state to instances
`_save_tasks`, all locks, counters and `_messages` are **class attributes**
(`etl_class.py:39-54`) — shared across all `EtlOptions` instances (e.g. two exchanges
in one process corrupt each other's save queues). Initialize them in `__init__`.
**Done (2026-06-13):** moved `_save_tasks`, the four locks, `_messages` and the four
counters into `__init__`; left class-level type annotations only. Verified two
`EtlDeribit` instances no longer share `_save_tasks`/locks.

### T6. Fix dependency declarations / packaging
- `psutil` (used by `exchange/cache.py`) and `requests` (used by
  `messanger/telegram.py`) are not declared — clean installs break on import of
  `alphavar.exchange` / `alphavar.messanger`. Prefer: drop `requests` (T8 switches to
  `httpx`), drop `psutil` (T12 removes the custom cache); otherwise declare them.
- `plotly` is imported directly but only available transitively via `chart-studio` —
  declare it explicitly.
- `alphavar.options_etl` ships in the wheel but `apscheduler` lives in a Poetry group
  that pip users can't install — expose it as a pip extra
  (`alphavar[etl]`) and make the import error actionable.

**Done (2026-06-13):** declared `numpy`, `plotly`, `requests`, `psutil` as core deps;
moved `apscheduler` to `optional = true` + `[tool.poetry.extras] etl = ["apscheduler"]`
(pip `alphavar[etl]`); wrapped the apscheduler import in `options_etl/etl_class.py` with
an actionable `ImportError`; regenerated `poetry.lock`; `poetry check` passes.
Note: `requests`/`psutil` are declared for correctness now but are slated for removal by
T8 (httpx) and T12 (cachetools).

### T6b. Migrate pyproject to PEP 621 `[project]` tables (non-blocking)
`poetry check` warns: deprecated license classifiers, deprecated `[tool.poetry.extras]`,
and `[tool.poetry.dependencies]` without `[project.dependencies]`. Migrate dependencies
and extras to the `[project]` table (`project.dependencies`,
`project.optional-dependencies`, `project.license`). Cosmetic/format-only; defer until
after the P0/P1 functional fixes land.
**Done (2026-06-13):** moved runtime deps to `[project.dependencies]` (PEP 508 specs),
the `etl` extra to `[project.optional-dependencies]`, dropped the deprecated GPL
license classifier (kept SPDX `license = "GPL-3.0-or-later"`). `[tool.poetry.dependencies]`
keeps only `python`; dev/test stay Poetry groups. `poetry lock`; `poetry check` → All set!

## P1 — Security

### T7. Treat the local Telegram token as exposed; add `test.env.example`
Local `test.env` contains a real-looking bot token (commented out). The file is
gitignored and the token is not in git history, but it should be revoked via BotFather
and replaced. Add a committed `test.env.example` (variable names, no values) and make
`DATA_PATH` default to a repo-relative path — the current absolute
`/home/akumidv/...` path breaks tests on any other machine.
**Done (2026-06-13, by user):** `DATA_PATH` repointed to the working tree; full suite
22 failed/71 err → 12 failed/114 passed/21 err. Token lives only in gitignored
`test.env` (not committed, not in history) — left as-is per owner. Remaining failures are
T11 (live network) / T19 (unimplemented chain load), not `DATA_PATH`. `test.env.example`
still worth adding for onboarding (optional).

### T8. Harden `TelegramMessanger` (`messanger/telegram.py`)
- Switch from `requests` to `httpx` (already a core dependency).
- The bot token is part of the request URL: ensure it never reaches logs/exception
  text (current `print(..., err)` can leak it).
- Check the response status — non-2xx is currently silently ignored, and only
  `ConnectionError`/`Timeout` are caught.
- `parse_mode='Markdown'` with unescaped report text makes sends fail on special
  characters — escape or send plain text. Fix the `[ERROR}` typo.
**Done (2026-06-13):** rewrote on `httpx` (dropped `requests` dep); token never logged
(`logger.error`, not `.exception`, no URL in messages); `raise_for_status` + typed
`httpx` handling; `parse_mode='MarkdownV2'` (configurable) + new `escape_markdown_v2()`
helper for callers to escape *data* (markup stays in report templates — T-followup: ETL
`_report` should escape interpolated asset names/errors); removed the meaningless VK
`random_id`; fixed the `[ERROR}` typo. `requests` removed from deps.

### T9. Validate path-building inputs (path traversal)
`asset_code` / `asset_name` / `exchange_code` are interpolated into filesystem paths in
`AbstractFileProvider._get_history_folder`, `PandasLocalFileProvider`, and
`EtlOptions.get_updates_folder` without validation — a crafted name containing `../`
escapes the data root. Add a shared validator (allowlist, e.g.
`^[A-Za-z0-9._-]+$`, reject `..`) applied in both provider and ETL layers.
**Done (2026-06-13):** added `options_lib/normalization/path_safety.py`
(`validate_path_segment`, allowlist `^[A-Za-z0-9._-]+$`, rejects `.`/`..`/separators/
empty). Applied at: `AbstractFileProvider.__init__` (exchange_code),
`_get_history_folder` (asset_code), `EtlOptions.get_updates_folder` (asset_name),
`EtlHistory.__init__` (exchange_code). Tests in `path_safety_test.py`; valid codes
(BTC, ETH_USDC, …) still pass.

### T8b. Drop `chart-studio` dependency (dead, pulls in `requests`)
`chart_studio` is never imported — all charting uses `plotly` directly (now a declared
dep). `chart-studio` is the only **hard** (non-optional) thing dragging `requests` into
the dependency tree (pandas does NOT require requests). Remove `chart-studio` from
`[project.dependencies]`; verify plotly rendering still works (offline `iplot`,
`graph_objects`). After this, `requests` leaves the runtime tree entirely, which
retroactively justifies the T8 httpx switch. P1/P2.
**Done (2026-06-13):** removed `chart-studio` from deps (never imported; plotly is
self-contained and does not require it), bumped `plotly` to `>=5.24,<7` (installed 6.3),
dropped the stale `chart_studio` code comment. `poetry lock` — `requests` now appears
only in the `dev` group, gone from runtime. Also fixed the T1b tail in
`tests/conftest.py` (`load_option_history`→`load_options_history`, `symbol=`→
`asset_code=`, `option_columns`→`options_columns`) — unblocked chart/analytic fixtures.
Note: 2 `risk_payoff` failures remain (`RISK_PNL_PREMIUM` column not produced by
`chain_payoff`) — pre-existing payoff-logic bug, unrelated; needs its own task.

### T10. Remove the misleading `signed` request parameter
`RequestClass.request_api(..., signed=False)` accepts `signed` but implements no
signing — callers may believe authenticated calls work. Remove the parameter (public
endpoints only) or implement explicit signing per R7. Also: raise `RequestException`
with `from err`, and add retry/backoff + HTTP 429 (rate-limit) handling for ETL-scale
polling of Deribit/MOEX.
**Done (2026-06-13):** `signed=True` now raises `NotImplementedError` (public endpoints
only) instead of silently sending unauthenticated; `from err` added on the JSON-parse
re-raise. `_request` retries 429/5xx + transport errors with exponential backoff
(honors `Retry-After` on 429), `MAX_RETRIES=3`, then surfaces `APIException`/
`RequestException`. Tests in `request_class_test.py` via `httpx.MockTransport`
(sleep patched). Signing itself still deferred (R7).

## P2 — Robustness and code quality

### T11. Make the test suite hermetic and green
Current clean-checkout run: 22 failed, 71 errors. Causes: stale absolute `DATA_PATH`
(see T7), live network calls in exchange unit tests (Deribit/MOEX APIs), and the T1
regression. Mock HTTP (e.g. `respx` for httpx), commit or generate a small parquet
fixture set, and gate any remaining integration tests behind a marker
(`-m integration`).

### T12. Replace the custom `Cache` with `cachetools`
`exchange/cache.py` is a hand-rolled cache with serious concurrency flaws: `_lock()`
ignores acquisition timeout (proceeds unlocked after 1 s), `_unlock()` can release a
lock held by another thread, bare `except:` everywhere, `sys.getsizeof(df)` does not
measure DataFrame memory (use `df.memory_usage(deep=True).sum()`), and a pandas
DataFrame is used as a concurrent metadata index. `cachetools` is already a declared
dependency — use `TTLCache` + a plain `threading.Lock`, drop `psutil`.

### T13. Introduce `logging` instead of `print`
ETL, exchanges and messengers log via `print(..., file=sys.stderr)`. Add a module-level
`logging` logger, keep messenger notifications separate from diagnostics.

### T14. Clean up `option_data_class.py` and silent data mutation
Remove the 4× duplicated imports (lines 4-21). Reconsider the silent
`dropna(subset=[PRICE])` inside the `df_hist` getter — dropping rows during lazy load
is surprising; make it explicit (parameter or documented enrichment step).

### T14b. Fix `chain_payoff` missing `RISK_PNL_PREMIUM` column
`tests/unit/options_lib/analytics/risk/risk_payoff_test.py` expects `chain_payoff` to
produce a `risk_pnl_premium` (`RCl.RISK_PNL_PREMIUM`) column alongside `risk_pnl`, but
the function only outputs `strike`/`risk_pnl` — 2 tests fail (`test_chain_pnl_risk_
profile_long_call`, `test__calc_premium_profile_long_call[200]`). Either compute the
premium-adjusted PnL column or update the contract/tests. Pre-existing logic bug,
surfaced 2026-06-13; unrelated to the rename/packaging work.

### T15. Add CI
No workflows exist (`.github/` has only `copilot-instructions.md`). Add a GitHub
Actions workflow: `poetry install --with etl,dev,test`, `pytest`, `pylint src/` on PR
and push to `main`. Depends on T11 for a green baseline.

### T16. Sync documentation with the post-rename layout
`AGENTS.md` and `docs/dev/PROJECT_OVERVIEW.md` still describe `src/options_lib/`,
`src/exchange/`, `src/provider/`, `src/options_etl/` as top-level packages — they all
live under `src/alphavar/` now. PROJECT_OVERVIEW also lists `pricer/`, `forecast/`,
`validation/` facade packages that do not exist — mark them as planned or remove.
Mention `ARCHITECTURE_REQUIREMENTS.md` and `TASKS.md` from `AGENTS.md`.

### T17. Repository hygiene
- Drop the tracked legacy tree `old/` (preserve via a git tag/branch if needed).
- Delete the untracked AI-chat artifact `options_pricing_backend.py` at the repo root.
- Remove committed `__pycache__` artifacts if any remain after T3.

### T18. Exception semantics in parsers
`DeribitMarket._kind_enrichment` raises builtin `SyntaxError` for data parse failures
and wraps it in a no-op `try/except ... raise err`. Introduce a dedicated
`InstrumentParseError` (in `exchange/exchange_exception.py`) and remove the dead
re-raise.

### T19. Finish or fence `PandasLocalFileProvider` period loading
`_load_data_for_period` is a `match type(...)` ladder where most branches raise
`NotImplementedError` (year-to-year, date-to-date, datetime). Implement multi-year
range loading (concat per-year files), replace exact-`type()` matching with
`isinstance` checks (mind `datetime` being a `date` subclass — check `datetime`
first), and replace the magic `"datetime"` column literal with the dictionary enum.

### T20. Vectorize Deribit book normalization
`_normalize_book` applies `_kind_enrichment` row-by-row (`df.apply(axis='columns')`
with a deep copy per row) over ~5000 instruments per snapshot — the dominant ETL cost.
Vectorize: split `instrument_name` with `str.extract`/`str.split` once, derive
kind/strike/expiration by masks.

## P3 — Later

### T21. Fill the planned facade components
`pricer/`, `forecast/`, `validation/` are described in the overview but absent. When
implemented, they must follow R3 (component class over shared `OptionData`, pure math
in `options_lib`).

### T22. Windows portability of ETL
`EtlOptions.HOST_NAME = os.uname()[1]` fails on Windows — use `platform.node()`.

### T23. Column dictionary v2: plain-string registry + pandera schemas
Decisions:
- Column labels in DataFrames are **plain `str`, always** — no enum objects, no str
  subclasses. Nothing ever needs renaming/normalizing before `to_parquet`.
- The registry becomes a namespace of string constants (`class Col:` with
  `STRIKE: Final = "strike"`), replacing the column enums and the `.nm` suffix.
  Uniqueness (the `@enum.unique` guarantee) is enforced by a unit test over
  `vars(Col)`.
- Column **metadata leaves the registry**: dtypes move to the pandera schema layer,
  `resample_func` moves to a `dict[str, str]` next to
  `normalization/timeframe_resample.py` (it is an engine-specific concern).
- Entity composition (which columns form options/futures/spot datasets) lives in the
  pandera model layer: mixins (timestamp/quote/OHLC/greeks) + entity models
  (`OptionsHistory`, `FuturesHistory`, `SpotHistory`, `OptionsBook`), every field bound
  to the registry via `pa.Field(alias=Col....)`. `Model.field` resolves to the plain
  alias string, so code may reference columns via `Col.X` or `Model.x` — same `str`.
- Validation at layer boundaries (provider/exchange normalize output; enrichment in
  dev mode) with `strict=False`, `coerce=True`, `lazy=True`; disabled in production
  ETL via pandera config. `pandera.pandas` now, `pandera.polars` after T24.

Execution order (each step keeps `pytest`/`pylint` green):
1. **T23.1** Add `Col` registry + uniqueness test; mechanical migration
   `OCl.X.nm` → `Col.X` (sed-able); delete the old column enums when no usages remain.
   Keep the typo string `"exhchange_mark_price"` as the value for now (data compat).
2. **T23.2** Replace `FuturesColumns`/`SpotColumns` and the derived
   `OPTION_NON_*_COLUMN_NAMES` lists with per-dataset `tuple[str, ...]` over `Col`.
3. **T23.3** Move dtype/resample metadata out of the dictionary (see decisions above);
   fix `DataEngine.POLARIS` typo (overlaps T24).
4. **T23.4** Add `pandera` dependency; define mixins + entity models with
   `alias=Col.*`; derive provider default column lists from the models.
5. **T23.5** Wire boundary validation + config switch (env var) to disable in prod.
6. **T23.6** Adopt the price/IV column model (R4.2). Semantics flip: `PRICE`/`IV` are
   now **our** normalized output (BS + smile fit + no-arb), not exchange data — so the
   exchange's real values get an `exch_` prefix and there is **no** `fair_*` pair.
   - `PRICE`/`IV` (`price`/`iv`): keep the names, but they become the project's model
     output (the pricer/normalizer writes them; raw exchange data must no longer land
     here directly).
   - Add `EXCH_PRICE`/`EXCH_IV` (`exch_price`/`exch_iv`) — the venue's traded/quoted
     price as received.
   - Replace `EXCHANGE_MARK_PRICE`/`EXCHANGE_MARK_IV` (typo `exhchange_…`) with
     `EXCH_MARK_PRICE`/`EXCH_MARK_IV` (`exch_mark_price`/`exch_mark_iv`) — Deribit
     `mark_price` and MOEX `theorprice` both map here.
   - Add `SETTLE_PRICE`/`SETTLE_IV` (`settle_price`/`settle_iv`), EOD-only, nullable
     intraday. No `exch_` prefix.
   - Rename `ORIGINAL_TIMESTAMP` (`original_timestamp`) → `EXCH_TIMESTAMP`
     (`exch_timestamp`) — it is the venue's own timestamp (Deribit `creation_timestamp`,
     MOEX `updatetime`), so it follows the `exch_` rule. `request_timestamp` and
     `timestamp` are ours and keep their names. Repoint the deribit/moex rename maps and
     the read-shim/migration below.
   - Remove the planned `MARK_PRICE`/`MARK_IV` and `FAIR_PRICE`/`FAIR_IV` entries —
     superseded.
   - Repoint Deribit/MOEX normalizers (`'mark_price'`/`'theorprice'` →
     `exch_mark_*`) and `COLUMNS_TO_CURRENCY`. Replace the `source_` prefix
     (`SOURCE_PREFIX`) with a `_raw` **suffix**: the pre-currency-conversion value of
     `<col>` is `<col>_raw` (`ask_raw`, `exch_mark_price_raw`, …). Stays narrow —
     currency conversion only (R4.2 group 3). `AbstractExchange.SOURCE_PREFIX` and the
     one site that applies it (`deribit.py:241`) change accordingly; `_raw` data in
     existing parquet under `source_*` needs the migration script too.
   - Read-shim on parquet load renaming old `exhchange_mark_price`/`exchange_mark_iv`
     → `exch_mark_price`/`exch_mark_iv`; one-off migration script for stored data.
   - **Caution:** before this lands, raw exchange price still flows into `price` via
     `fill_option_price`. Splitting "what the exchange sent" (`exch_*`) from "our
     model output" (`price`) requires the pricer to exist or `price` to be explicitly
     sourced from `exch_price` until it does — decide the interim behavior so `price`
     is never silently empty.

### T23.7. Pluralize collection identifiers (R4.1)
Bare singular `option`/`future` identifiers that denote collections: rename
`BookData.option`/`.future` → `.options`/`.futures` (`exchange/_abstract_exchange.py`)
and the `option = []` accumulator in `moex.py:304`. Audit that no bare singular
`option`/`future` denotes a single entity (single-instrument attributes like
`option_type` stay singular). Mechanical; do alongside T23.1.

### T23.8. Align facade class names with the singular/plural rule (R4.1)
Class names are inconsistent: the facade components operate on a *set* of options
(`df_hist` is many rows) but are singular, while the dictionary classes for the same
domain are plural. Rename to plural (public API change — do as one commit, update all
imports + tests + docs):
`OptionData`→`OptionsData`, `OptionChain`→`OptionsChain`,
`OptionEnrichment`→`OptionsEnrichment`, `OptionAnalytic`→`OptionsAnalytic`
(and `OptionAnalyticPrice`/`OptionAnalyticRisk`→`OptionsAnalytic…`).
Keep `Option` singular — it is the single-instrument facade/entity. Already-correct:
`OptionsColumns`, `OptionsLeg`, `OptionsType`, `OptionsStyle`, `OptionsPriceStatus`,
`FuturesColumns`. Files: `option_class.py`/`option_data_class.py` keep their names
(they host the singular `Option` entry point); a module about the options dataset uses
the plural form.

### T24. Polars readiness (see R8)
Polars is the strategic target engine. Preparatory steps while still on pandas:
- Fix `DataEngine.POLARIS = "polaris"` → `POLARS = "polars"`
  (`provider/_provider_entities.py:14`).
- Remove engine-specific types from the dictionary's public contract
  (`EnumDataFrameColumn.type` currently holds `pd.Timestamp`); move dtype mapping to
  the per-engine schema layer from T23.
- Audit `options_lib` for hard-to-port idioms (row-wise `apply`, index reliance,
  `inplace=True`) — overlaps with T20.
