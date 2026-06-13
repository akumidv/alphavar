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

### T2. Fix `SaveTask` mutation bug in ETL save path
`SaveTask` is a `NamedTuple`, but `EtlOptions._save_task_dataframe()` ends with
`save_task.df = None` (`etl_class.py:347`) — raises `AttributeError` on every save.
Convert `SaveTask` to a `@dataclass` (it is mutated) or drop the mutation.

### T3. Remove duplicated `src/options_etl/` package
`src/options_etl/` is a diverged pre-rename copy of `src/alphavar/options_etl/` with
stale `from options_etl...` imports. It is not shipped in the wheel and silently drifts
from the real code. Delete it; keep only `src/alphavar/options_etl/`. Check `demo/`
scripts for imports of the old path.

### T4. Fix dead exception handling around thread pools
`executor.map()` raises on iteration — it never yields `Exception` objects, so:
- `EtlOptions._book_snapshot_timeframe_job` (`etl_class.py:241`): the
  `isinstance(book_data, Exception)` branch is dead; one failing asset aborts the whole
  job loop and remaining assets are lost for that timeframe tick.
- `DeribitExchange.get_options_assets_books_snapshot` (`deribit.py:367-371`):
  `job_res.result()` raises; the `isinstance(..., Exception)` check is dead code.
Use `submit()` + `as_completed()` with per-task `try/except`, log the failed asset,
continue with the rest.

### T5. Move `EtlOptions` mutable state to instances
`_save_tasks`, all locks, counters and `_messages` are **class attributes**
(`etl_class.py:39-54`) — shared across all `EtlOptions` instances (e.g. two exchanges
in one process corrupt each other's save queues). Initialize them in `__init__`.

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

## P1 — Security

### T7. Treat the local Telegram token as exposed; add `test.env.example`
Local `test.env` contains a real-looking bot token (commented out). The file is
gitignored and the token is not in git history, but it should be revoked via BotFather
and replaced. Add a committed `test.env.example` (variable names, no values) and make
`DATA_PATH` default to a repo-relative path — the current absolute
`/home/akumidv/...` path breaks tests on any other machine.

### T8. Harden `TelegramMessanger` (`messanger/telegram.py`)
- Switch from `requests` to `httpx` (already a core dependency).
- The bot token is part of the request URL: ensure it never reaches logs/exception
  text (current `print(..., err)` can leak it).
- Check the response status — non-2xx is currently silently ignored, and only
  `ConnectionError`/`Timeout` are caught.
- `parse_mode='Markdown'` with unescaped report text makes sends fail on special
  characters — escape or send plain text. Fix the `[ERROR}` typo.

### T9. Validate path-building inputs (path traversal)
`asset_code` / `asset_name` / `exchange_code` are interpolated into filesystem paths in
`AbstractFileProvider._get_history_folder`, `PandasLocalFileProvider`, and
`EtlOptions.get_updates_folder` without validation — a crafted name containing `../`
escapes the data root. Add a shared validator (allowlist, e.g.
`^[A-Za-z0-9._-]+$`, reject `..`) applied in both provider and ETL layers.

### T10. Remove the misleading `signed` request parameter
`RequestClass.request_api(..., signed=False)` accepts `signed` but implements no
signing — callers may believe authenticated calls work. Remove the parameter (public
endpoints only) or implement explicit signing per R7. Also: raise `RequestException`
with `from err`, and add retry/backoff + HTTP 429 (rate-limit) handling for ETL-scale
polling of Deribit/MOEX.

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
6. **T23.6** Rename `exhchange_mark_price` → `exchange_mark_price`: change the `Col`
   value, keep a read-shim (rename on parquet load), write a one-off migration script
   for stored data.

### T24. Polars readiness (see R8)
Polars is the strategic target engine. Preparatory steps while still on pandas:
- Fix `DataEngine.POLARIS = "polaris"` → `POLARS = "polars"`
  (`provider/_provider_entities.py:14`).
- Remove engine-specific types from the dictionary's public contract
  (`EnumDataFrameColumn.type` currently holds `pd.Timestamp`); move dtype mapping to
  the per-engine schema layer from T23.
- Audit `options_lib` for hard-to-port idioms (row-wise `apply`, index reliance,
  `inplace=True`) — overlaps with T20.
