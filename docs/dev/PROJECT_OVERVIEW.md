# Project Overview — alphavar

> A document for developing and extending the project, including with the help of AI
> assistants (Claude, GitHub Copilot, etc.). It describes the architecture, modules,
> extension points, and code conventions. It complements `AGENTS.md` and `README.md`.
>
> **Project status:** under active development (developing stage). The API may change.

---

## 1. Purpose

`alphavar` is a Python library for analyzing and visualizing options (and futures).
The name reads as **alpha + VaR** (alpha = returns above the market, VaR = Value-at-Risk).
It provides a single interface for:

- retrieving options/futures data from various sources (exchange APIs and local files);
- enriching data with computed metrics (intrinsic/time value, ATM/ITM/OTM, Greeks);
- working with option chains and building "desks";
- risk analytics (payoff of combinations) and time-value analysis;
- visualization (Plotly/matplotlib);
- ETL processes for accumulating historical snapshots of quotes.

**Language:** Python `^3.11`. **Package manager:** Poetry (`package-mode = false`).

---

## 2. Repository map

```
alphavar/
├── src/
│   ├── alphavar/   # PUBLIC API — the Option facade and its components
│   │   ├── option_class.py          # Option class (main entry point)
│   │   ├── option_data_class.py     # OptionData — data management
│   │   ├── enrichment/              # OptionEnrichment
│   │   ├── chain/                   # OptionChain
│   │   ├── analytic/                # OptionAnalytic (risk + price)
│   │   ├── chart/                   # ChartClass (Plotly)
│   │   ├── pricer/                  # fair value calculation (stub)
│   │   ├── forecast/                # price forecasting (stub)
│   │   └── validation/              # data validation
│   │
│   ├── options_lib/         # BUSINESS LOGIC (implementation, no provider state)
│   │   ├── dictionary/              # all enums and DataFrame column descriptions
│   │   ├── entities/                # Pydantic entities (OptionsLeg, etc.)
│   │   ├── enrichment/              # pure enrichment functions
│   │   ├── chain/                   # chain selection, ATM/ITM/OTM, desk
│   │   ├── normalization/           # price/date normalization, timeframe resampling
│   │   ├── analytic/                # payoff (risk) + time values (price)
│   │   └── chart/                   # chart data preparation
│   │
│   ├── provider/            # Data source abstraction
│   │   ├── _abstract_provider_class.py   # AbstractProvider (interface)
│   │   ├── _provider_entities.py         # RequestParameters
│   │   └── _local_provider.py            # PandasLocalFileProvider (Parquet)
│   │
│   ├── exchange/            # Exchange implementations (inherit AbstractProvider)
│   │   ├── _abstract_exchange.py    # AbstractExchange + RequestClass (httpx)
│   │   ├── deribit.py               # DeribitExchange (crypto)
│   │   ├── moex.py                  # MoexExchange (RU)
│   │   ├── binance.py               # BinanceExchange
│   │   ├── cache.py                 # API TTL cache
│   │   ├── exchange_fabric.py       # ExchangeFabric (factory)
│   │   └── exchange_provider_factory.py
│   │
│   ├── options_etl/         # ETL — accumulating quote snapshots
│   │   ├── etl_class.py             # EtlOptions (base, APScheduler)
│   │   ├── deribit_etl.py           # EtlDeribit
│   │   ├── moex_etl.py              # EtlMoex
│   │   └── etl_updates_to_history.py
│   │
│   └── messanger/           # Notifications (Telegram / console)
│
├── tests/                   # pytest, see §9
├── demo/                    # example notebooks (incl. for Google Colab)
├── docs/                    # documentation site (Next.js + Markdoc)
│   └── dev/                 # development docs (this file)
├── pyproject.toml           # dependencies, pytest/pylint config
├── test.env                 # environment variables for tests
├── AGENTS.md                # guidance for AI agents (CLAUDE.md links here)
└── README.md
```

> ⚠️ **Note:** the library directory is named `src/options_lib/` (NOT `src/option_lib/`).
> Follow the code if you see the outdated spelling `option_lib` anywhere.

---

## 3. Architecture: key layers

```
┌─────────────────────────────────────────────────────────┐
│  alphavar/  — the Option facade (stateful, public)       │
│    Option → {OptionData, OptionEnrichment, OptionChain,   │
│              OptionAnalytic, ChartClass}                  │
└───────────────┬───────────────────────────────────────────┘
                │ uses pure logic
┌───────────────▼───────────────────────────────────────────┐
│  options_lib/  — stateless functions (DataFrame in/out)    │
│    dictionary, entities, enrichment, chain, normalization, │
│    analytic, chart                                         │
└───────────────┬───────────────────────────────────────────┘
                │ obtains data through
┌───────────────▼───────────────────────────────────────────┐
│  provider/  — AbstractProvider (data source interface)     │
│    ├─ PandasLocalFileProvider (Parquet files)              │
│    └─ exchange/ — DeribitExchange, MoexExchange, Binance…  │
└────────────────────────────────────────────────────────────┘
```

**Separation principle:**
- `alphavar/*` — stateful classes (hold the DataFrame, provider, parameters).
- `options_lib/*` — pure functions/utilities that take and return a `pandas.DataFrame`.
- `provider/` + `exchange/` — deliver raw data.

Keep this separation in mind when extending: **new computational logic goes into
`options_lib`, a new data source goes into `provider`/`exchange`, and a convenient
API method goes into `alphavar`.**

---

## 4. Main facade — the `Option` class

`src/alphavar/option_class.py`

```python
class Option:
    """Base option class to work with option data different ways."""
    def __init__(self, provider: AbstractProvider, option_symbol: str,
                 params: RequestParameters | None = None,
                 option_columns: list | None = None,
                 future_columns: list | None = None)
```

It aggregates five components (each receives the shared `OptionData` via DI):

| Component | Class | File | Purpose |
|-----------|-------|------|---------|
| `data` | `OptionData` | `option_data_class.py` | load/store `df_hist`, `df_fut`, `df_chain` |
| `enrichment` | `OptionEnrichment` | `enrichment/_enrichment_class.py` | computed columns |
| `chain` | `OptionChain` | `chain/_chain_class.py` | chains, ATM/ITM/OTM, desk |
| `analytic` | `OptionAnalytic` | `analytic/analytic_class.py` | risk (payoff) + time value |
| `chart` | `ChartClass` | `chart/chart_class.py` | visualization (Plotly) |

### OptionData
- Properties: `option_symbol`, `period_from`, `period_to`, `timeframe`.
- DataFrames: `df_hist` (options), `df_fut` (futures), `df_chain` (chain).
- `update_option_chain()` — load the chain via the provider.

### OptionEnrichment
- `enrich_options(columns, force)` — add columns with automatic dependency resolution
  (`OPTION_COLUMNS_DEPENDENCIES`).
- Supports: `UNDERLYING_PRICE`, `INTRINSIC_VALUE`, `TIMED_VALUE`, `PRICE_STATUS`.

### OptionChain
- `select_chain()`, `add_atm_itm_otm()`, `get_atm_strike()`,
  `get_atm_nearest_strikes()`, `get_desk()`.

### OptionAnalytic
- `.risk` → `OptionAnalyticRisk` — payoff of combinations (`OptionsLeg` legs).
- `.price` → `OptionAnalyticPrice` — time-value series
  (`time_value_series_by_strike_to_atm_distance()`, `time_value_series_by_atm_distance()`).

### ChartClass
- `.price` → `ChartPriceClass`; methods `show()`, `init(title)`,
  `time_values()`, `time_values_for_strike()`, `time_values_for_distance()`.

---

## 5. Data dictionary (`options_lib/dictionary/`)

DataFrame columns are described by **enums** (not string literals) — use them when
extending the code instead of "magic strings".

| Enum | Values / purpose |
|------|------------------|
| `OptionsColumns` | 40+ columns: `TIMESTAMP`, `STRIKE`, `EXPIRATION_DATE`, `OPTION_TYPE`, `PRICE`, `ASK`, `BID`, `OPEN_INTEREST`, `VOLUME`, `UNDERLYING_PRICE`, `INTRINSIC_VALUE`, `TIMED_VALUE`, `PRICE_STATUS`, Greeks `DELTA/GAMMA/VEGA/THETA/RHO`, metadata `ASSET_CODE/ASSET_TYPE/CURRENCY/OPTION_STYLE` |
| `FuturesColumns` | futures columns |
| `SpotColumns` | spot columns |
| `OptionsType` | `CALL` ("call"/"c"), `PUT` ("put"/"p") |
| `OptionsPriceStatus` | `ATM`, `ITM`, `OTM` |
| `OptionsStyle` | `AMERICAN`, `EUROPEAN` |
| `AssetKind` | `OPTIONS`, `FUTURES`, `SPOT` |
| `AssetType` | `SHARE`, `COMMODITY`, `INDEX`, `CURRENCY`, `CRYPTO` |
| `Timeframe` | `EOD`, `1m`, `5m`, `15m`, `30m`, `1h`, `4h` (with `mult`/`offset`) |
| `LegType` | `OPTIONS_CALL`, `OPTIONS_PUT`, `FUTURES` |
| `Currency` | currency codes |

**Column dependencies during enrichment:**
```python
OPTION_COLUMNS_DEPENDENCIES = {
    INTRINSIC_VALUE: [UNDERLYING_PRICE],
    TIMED_VALUE:     [INTRINSIC_VALUE],
    PRICE_STATUS:    [UNDERLYING_PRICE],
}
```

**Key entity** (`options_lib/entities/`):
```python
class OptionsLeg(BaseModel):
    strike: float
    lots: int
    type: LegType   # a leg of an options/futures combination
```

---

## 6. Data providers

### The `AbstractProvider` interface (`provider/_abstract_provider_class.py`)
```python
class AbstractProvider(ABC):
    exchange_code: str
    options_columns: list
    futures_columns: list

    def get_assets_list(asset_kind: AssetKind) -> list[str]: ...
    def get_asset_history_years(asset_code, asset_kind, timeframe) -> list[int]: ...
    def load_options_history(asset_code, params, columns) -> pd.DataFrame: ...
    def load_options_book(asset_code, settlement_datetime, timeframe) -> pd.DataFrame: ...
    def load_futures_history(asset_code, params, columns) -> pd.DataFrame: ...
    def load_futures_book(asset_code, settlement_datetime, timeframe) -> pd.DataFrame: ...
    def load_options_chain(asset_code, settlement_datetime, expiration_date) -> pd.DataFrame | None: ...
```

### `RequestParameters` (`provider/_provider_entities.py`)
```python
class RequestParameters(BaseModel):
    period_from: int | date | datetime | None = None
    period_to:   int | date | datetime | None = None
    timeframe:   Timeframe = Timeframe.EOD
```

### Implementations
- **`PandasLocalFileProvider`** (`provider/_local_provider.py`) — Parquet from disk.
  Path structure: `{exchange_code}/{asset_code}/{asset_kind}/{timeframe}/{year}.parquet`.
- **`AbstractExchange`** (`exchange/_abstract_exchange.py`) — subclass of `AbstractProvider`
  with a `RequestClass` (httpx) and `request_api(endpoint_path, signed=False, **kwargs)`.
  - `DeribitExchange` (`deribit.py`) — crypto futures/options/spot (+ combo).
  - `MoexExchange` (`moex.py`) — MOEX ISS option-calc.
  - `BinanceExchange` (`binance.py`).
- Cache: `exchange/cache.py` — TTL cache (128 items, reset at midnight).
- Factories: `ExchangeFabric`, `ExchangeProviderFactory`.

---

## 7. ETL (`options_etl/`)

Accumulation of quote snapshots on a schedule (APScheduler).

- **`EtlOptions`** (`etl_class.py`) — base class.
  Parameters: `exchange`, `asset_names`, `timeframe`, `update_data_path`, `timeframe_cron`.
  Uses a `ThreadPoolExecutor` for parallel loading; background heartbeat/report/save tasks.
  Structures: `AssetBookData` (option/future/spot snapshot), `SaveTask`.
- **`EtlDeribit`** (`deribit_etl.py`) — extended `AssetBookData` (`future_combo`,
  `option_combo`), `get_symbols_books_snapshot()`, `_save_timeframe_book_update()`.
- **`EtlMoex`** (`moex_etl.py`).
- **`etl_updates_to_history.py`** — integrate accumulated updates into history.

**Data volume estimate (Deribit):** 1m ≈ 275 GB/year, 5m ≈ 60 GB/year, 1h ≈ 4.5 GB/year.

---

## 8. Dependencies (`pyproject.toml`)

**Core:** `pandas ^2.2.3`, `pydantic ^2.10.5`, `pyarrow ^21`, `httpx ^0.28.1`,
`matplotlib ^3.9`, `chart-studio ^1.1`, `cachetools 6.2.0`, `python-dotenv ^1`.

**Groups (optional):**
- `etl`: `apscheduler ^3.11`
- `dev`: `setuptools`, `jupyter`, `pylint`
- `test`: `pytest`, `pytest-asyncio`, `pytest-dotenv`

Install: `poetry install --with etl,dev,test`

---

## 9. Tests

- Directory `tests/unit/{etl,exchange,provider,messanger}/`.
- pytest config (`pyproject.toml`): `pythonpath=["src"]`, `env_files=["test.env"]`,
  `testpaths=["tests"]`.
- Main fixtures (`tests/conftest.py`): `data_path`, `exchange_provider`
  (`PandasLocalFileProvider`), `option_data`, `option_symbol` (default `'BTC'`),
  `exchange_code` (`'DERIBIT'`), `provider_params`, lists of update files.
  Data is cached via the `_CACHE` dictionary.
- Run: `pytest`. Lint: `pylint src/`.

---

## 10. Configuration / environment

Variables (`test.env` and runtime):
- `DATA_PATH` — root of local Parquet data.
- `ETL_TIMEFRAME` — ETL timeframe (`5m`, `1h`, …).
- `TG_BOT_TOKEN`, `TG_CHAT` — Telegram notifications (optional).

Other: `.editorconfig` (max line 120), `sonar-project.properties` (SonarQube),
pylint (`max-line-length=120`, `max-args=8`, `max-positional-arguments=6`).

---

## 11. Extension points (how to extend)

| Task | Where to change | How |
|------|-----------------|-----|
| Add a new data source | `src/exchange/` | a new subclass of `AbstractExchange`, implement the abstract methods; register it in the factories |
| Add a computed column | `options_lib/enrichment/` + `dictionary/_dataframe_columns.py` | a new function + an entry in `OptionsColumns` and, if needed, in `OPTION_COLUMNS_DEPENDENCIES`; wire it into `OptionEnrichment` |
| New analytics | `options_lib/analytic/` + a wrapper in `alphavar/analytic/` | a pure function over a DataFrame + a facade method |
| New chart type | `options_lib/chart/` + `alphavar/chart/` | data preparation + a render method |
| New ETL source | `options_etl/` | a subclass of `EtlOptions` |
| Notification channel | `messanger/` | a subclass of `AbstractMessanger` |

**Code conventions:**
- DataFrame columns — only via the `OptionsColumns`/`FuturesColumns` enums, not strings.
- Pydantic models for entities and request parameters.
- Pure logic (no I/O or state) lives in `options_lib`; state and the provider live in `alphavar`.
- Lines ≤ 120 characters; docstrings are not required for private (`_`) and test (`test_`) functions.

---

## 12. Known caveats / TODO for future work

- The project is at an early development stage — the public API is unstable.
- `pricer/`, `forecast/`, `validation/` in `alphavar/` are stubs and need filling in.
- `BinanceExchange` is a minimal implementation.

---

## 13. Quick start for an AI assistant (Copilot, etc.)

1. The source of truth on architecture is this file + the code in `src/`. `AGENTS.md` is the guidance for AI agents (`CLAUDE.md` links to it).
2. Start reading from `src/alphavar/option_class.py` (the facade) and
   `src/options_lib/dictionary/` (the column and enum dictionary).
3. Before changing data logic, check `OPTION_COLUMNS_DEPENDENCIES`.
4. For a new exchange, copy the pattern in `src/exchange/deribit.py`.
5. Tests are required: place them in `tests/unit/<area>/` and reuse existing fixtures.
6. Verify with `pytest` and `pylint src/` before committing.
