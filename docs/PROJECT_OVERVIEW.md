# Project Overview — options_assembler

> Документ для разработки и доработки проекта, в том числе с помощью AI-ассистентов
> (Claude, GitHub Copilot и др.). Описывает архитектуру, модули, точки расширения и
> соглашения кода. Дополняет `CLAUDE.md` и `README.md`.
>
> **Статус проекта:** в активной разработке (developing stage). API может меняться.

---

## 1. Назначение

`options_assembler` — Python-библиотека для анализа и визуализации опционов (и фьючерсов).
Предоставляет единый интерфейс для:

- получения данных опционов/фьючерсов из разных источников (биржевые API и локальные файлы);
- обогащения данных вычисляемыми метриками (внутренняя/временная стоимость, ATM/ITM/OTM, Greeks);
- работы с цепочками опционов (option chains) и построения «столов» (desks);
- аналитики риска (payoff комбинаций) и временной стоимости;
- визуализации (Plotly/matplotlib);
- ETL-процессов для накопления исторических снимков котировок.

**Язык:** Python `^3.11`. **Менеджер пакетов:** Poetry (`package-mode = false`).

---

## 2. Карта репозитория

```
options_assembler/
├── src/
│   ├── options_assembler/   # ПУБЛИЧНЫЙ API — фасад Option и его компоненты
│   │   ├── option_class.py          # класс Option (главная точка входа)
│   │   ├── option_data_class.py     # OptionData — управление данными
│   │   ├── enrichment/              # OptionEnrichment
│   │   ├── chain/                   # OptionChain
│   │   ├── analytic/                # OptionAnalytic (risk + price)
│   │   ├── chart/                   # ChartClass (Plotly)
│   │   ├── pricer/                  # расчёт fair value (заготовка)
│   │   ├── forecast/                # прогноз цены (заготовка)
│   │   └── validation/              # валидация данных
│   │
│   ├── options_lib/         # БИЗНЕС-ЛОГИКА (реализация, без состояния провайдера)
│   │   ├── dictionary/              # все enum'ы и описания колонок DataFrame
│   │   ├── entities/                # Pydantic-сущности (OptionsLeg и др.)
│   │   ├── enrichment/              # чистые функции обогащения
│   │   ├── chain/                   # выбор цепочки, ATM/ITM/OTM, desk
│   │   ├── normalization/           # нормализация цен, дат, ресэмплинг таймфреймов
│   │   ├── analytic/                # payoff (risk) + time values (price)
│   │   └── chart/                   # подготовка данных для графиков
│   │
│   ├── provider/            # Абстракция источников данных
│   │   ├── _abstract_provider_class.py   # AbstractProvider (интерфейс)
│   │   ├── _provider_entities.py         # RequestParameters
│   │   └── _local_provider.py            # PandasLocalFileProvider (Parquet)
│   │
│   ├── exchange/            # Реализации бирж (наследуют AbstractProvider)
│   │   ├── _abstract_exchange.py    # AbstractExchange + RequestClass (httpx)
│   │   ├── deribit.py               # DeribitExchange (crypto)
│   │   ├── moex.py                  # MoexExchange (РФ)
│   │   ├── binance.py               # BinanceExchange
│   │   ├── cache.py                 # TTL-кэш API
│   │   ├── exchange_fabric.py       # ExchangeFabric (factory)
│   │   └── exchange_provider_factory.py
│   │
│   ├── options_etl/         # ETL — накопление снимков котировок
│   │   ├── etl_class.py             # EtlOptions (базовый, APScheduler)
│   │   ├── deribit_etl.py           # EtlDeribit
│   │   ├── moex_etl.py              # EtlMoex
│   │   └── etl_updates_to_history.py
│   │
│   └── messanger/           # Уведомления (Telegram / консоль)
│
├── tests/                   # pytest, см. §9
├── demo/                    # ноутбуки-примеры (в т.ч. для Google Colab)
├── docs/                    # сайт документации (Next.js + Markdoc)
├── pyproject.toml           # зависимости, конфиг pytest/pylint
├── test.env                 # переменные окружения для тестов
├── CLAUDE.md                # инструкции для Claude Code
└── README.md
```

> ⚠️ **Важно:** каталог библиотеки называется `src/options_lib/` (НЕ `src/option_lib/`).
> В `CLAUDE.md` встречается устаревшее написание `option_lib` — ориентируйтесь на код.

---

## 3. Архитектура: ключевые слои

```
┌─────────────────────────────────────────────────────────┐
│  options_assembler/  — фасад Option (stateful, публичный) │
│    Option → {OptionData, OptionEnrichment, OptionChain,   │
│              OptionAnalytic, ChartClass}                  │
└───────────────┬───────────────────────────────────────────┘
                │ использует чистую логику
┌───────────────▼───────────────────────────────────────────┐
│  options_lib/  — функции без состояния (DataFrame in/out)  │
│    dictionary, entities, enrichment, chain, normalization, │
│    analytic, chart                                         │
└───────────────┬───────────────────────────────────────────┘
                │ получает данные через
┌───────────────▼───────────────────────────────────────────┐
│  provider/  — AbstractProvider (интерфейс источников)      │
│    ├─ PandasLocalFileProvider (Parquet-файлы)              │
│    └─ exchange/ — DeribitExchange, MoexExchange, Binance…  │
└────────────────────────────────────────────────────────────┘
```

**Принцип разделения:**
- `options_assembler/*` — классы с состоянием (хранят DataFrame, провайдер, параметры).
- `options_lib/*` — чистые функции/утилиты, принимают и возвращают `pandas.DataFrame`.
- `provider/` + `exchange/` — поставка сырых данных.

Это разделение удобно держать в голове при доработке: **новую вычислительную логику
добавляют в `options_lib`, новый источник данных — в `provider`/`exchange`,
а удобный API-метод — в `options_assembler`.**

---

## 4. Главный фасад — класс `Option`

`src/options_assembler/option_class.py`

```python
class Option:
    """Base option class to work with option data different ways."""
    def __init__(self, provider: AbstractProvider, option_symbol: str,
                 params: RequestParameters | None = None,
                 option_columns: list | None = None,
                 future_columns: list | None = None)
```

Агрегирует пять компонентов (каждый получает общий `OptionData` через DI):

| Компонент | Класс | Файл | Назначение |
|-----------|-------|------|------------|
| `data` | `OptionData` | `option_data_class.py` | загрузка/хранение `df_hist`, `df_fut`, `df_chain` |
| `enrichment` | `OptionEnrichment` | `enrichment/_enrichment_class.py` | вычисляемые колонки |
| `chain` | `OptionChain` | `chain/_chain_class.py` | цепочки, ATM/ITM/OTM, desk |
| `analytic` | `OptionAnalytic` | `analytic/analytic_class.py` | риск (payoff) + временная стоимость |
| `chart` | `ChartClass` | `chart/chart_class.py` | визуализация (Plotly) |

### OptionData
- Свойства: `option_symbol`, `period_from`, `period_to`, `timeframe`.
- DataFrame'ы: `df_hist` (опционы), `df_fut` (фьючерсы), `df_chain` (цепочка).
- `update_option_chain()` — подгрузка цепочки через провайдера.

### OptionEnrichment
- `enrich_options(columns, force)` — добавить колонки с автоматическим разрешением
  зависимостей (`OPTION_COLUMNS_DEPENDENCIES`).
- Поддерживает: `UNDERLYING_PRICE`, `INTRINSIC_VALUE`, `TIMED_VALUE`, `PRICE_STATUS`.

### OptionChain
- `select_chain()`, `add_atm_itm_otm()`, `get_atm_strike()`,
  `get_atm_nearest_strikes()`, `get_desk()`.

### OptionAnalytic
- `.risk` → `OptionAnalyticRisk` — payoff комбинаций (ноги `OptionsLeg`).
- `.price` → `OptionAnalyticPrice` — ряды временной стоимости
  (`time_value_series_by_strike_to_atm_distance()`, `time_value_series_by_atm_distance()`).

### ChartClass
- `.price` → `ChartPriceClass`; методы `show()`, `init(title)`,
  `time_values()`, `time_values_for_strike()`, `time_values_for_distance()`.

---

## 5. Словарь данных (`options_lib/dictionary/`)

Колонки DataFrame описаны **enum'ами** (а не строковыми литералами) — при доработке
используйте их, а не «магические строки».

| Enum | Значения / назначение |
|------|------------------------|
| `OptionsColumns` | 40+ колонок: `TIMESTAMP`, `STRIKE`, `EXPIRATION_DATE`, `OPTION_TYPE`, `PRICE`, `ASK`, `BID`, `OPEN_INTEREST`, `VOLUME`, `UNDERLYING_PRICE`, `INTRINSIC_VALUE`, `TIMED_VALUE`, `PRICE_STATUS`, греки `DELTA/GAMMA/VEGA/THETA/RHO`, метаданные `ASSET_CODE/ASSET_TYPE/CURRENCY/OPTION_STYLE` |
| `FuturesColumns` | колонки фьючерсов |
| `SpotColumns` | колонки спота |
| `OptionsType` | `CALL` ("call"/"c"), `PUT` ("put"/"p") |
| `OptionsPriceStatus` | `ATM`, `ITM`, `OTM` |
| `OptionsStyle` | `AMERICAN`, `EUROPEAN` |
| `AssetKind` | `OPTIONS`, `FUTURES`, `SPOT` |
| `AssetType` | `SHARE`, `COMMODITY`, `INDEX`, `CURRENCY`, `CRYPTO` |
| `Timeframe` | `EOD`, `1m`, `5m`, `15m`, `30m`, `1h`, `4h` (с `mult`/`offset`) |
| `LegType` | `OPTIONS_CALL`, `OPTIONS_PUT`, `FUTURES` |
| `Currency` | коды валют |

**Зависимости колонок при обогащении:**
```python
OPTION_COLUMNS_DEPENDENCIES = {
    INTRINSIC_VALUE: [UNDERLYING_PRICE],
    TIMED_VALUE:     [INTRINSIC_VALUE],
    PRICE_STATUS:    [UNDERLYING_PRICE],
}
```

**Ключевая сущность** (`options_lib/entities/`):
```python
class OptionsLeg(BaseModel):
    strike: float
    lots: int
    type: LegType   # нога комбинации опционов/фьючерсов
```

---

## 6. Провайдеры данных

### Интерфейс `AbstractProvider` (`provider/_abstract_provider_class.py`)
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

### Реализации
- **`PandasLocalFileProvider`** (`provider/_local_provider.py`) — Parquet с диска.
  Структура путей: `{exchange_code}/{asset_code}/{asset_kind}/{timeframe}/{year}.parquet`.
- **`AbstractExchange`** (`exchange/_abstract_exchange.py`) — наследник `AbstractProvider`
  с `RequestClass` (httpx) и `request_api(endpoint_path, signed=False, **kwargs)`.
  - `DeribitExchange` (`deribit.py`) — crypto futures/options/spot (+ combo).
  - `MoexExchange` (`moex.py`) — ISS MOEX option-calc.
  - `BinanceExchange` (`binance.py`).
- Кэш: `exchange/cache.py` — TTL-кэш (128 элементов, сброс в полночь).
- Фабрики: `ExchangeFabric`, `ExchangeProviderFactory`.

---

## 7. ETL (`options_etl/`)

Накопление снимков котировок по расписанию (APScheduler).

- **`EtlOptions`** (`etl_class.py`) — базовый класс.
  Параметры: `exchange`, `asset_names`, `timeframe`, `update_data_path`, `timeframe_cron`.
  `ThreadPoolExecutor` для параллельной загрузки; фоновые задачи heartbeat/report/save.
  Структуры: `AssetBookData` (снимок option/future/spot), `SaveTask`.
- **`EtlDeribit`** (`deribit_etl.py`) — расширенная `AssetBookData` (`future_combo`,
  `option_combo`), `get_symbols_books_snapshot()`, `_save_timeframe_book_update()`.
- **`EtlMoex`** (`moex_etl.py`).
- **`etl_updates_to_history.py`** — интеграция накопленных обновлений в историю.

**Оценка объёма данных (Deribit):** 1m ≈ 275 ГБ/год, 5m ≈ 60 ГБ/год, 1h ≈ 4.5 ГБ/год.

---

## 8. Зависимости (`pyproject.toml`)

**Core:** `pandas ^2.2.3`, `pydantic ^2.10.5`, `pyarrow ^21`, `httpx ^0.28.1`,
`matplotlib ^3.9`, `chart-studio ^1.1`, `cachetools 6.2.0`, `python-dotenv ^1`.

**Группы (опциональные):**
- `etl`: `apscheduler ^3.11`
- `dev`: `setuptools`, `jupyter`, `pylint`
- `test`: `pytest`, `pytest-asyncio`, `pytest-dotenv`

Установка: `poetry install --with etl,dev,test`

---

## 9. Тесты

- Каталог `tests/unit/{etl,exchange,provider,messanger}/`.
- Конфиг pytest (`pyproject.toml`): `pythonpath=["src"]`, `env_files=["test.env"]`,
  `testpaths=["tests"]`.
- Главные fixtures (`tests/conftest.py`): `data_path`, `exchange_provider`
  (`PandasLocalFileProvider`), `option_data`, `option_symbol` (по умолч. `'BTC'`),
  `exchange_code` (`'DERIBIT'`), `provider_params`, списки файлов обновлений.
  Кэширование данных через словарь `_CACHE`.
- Запуск: `pytest`. Линт: `pylint src/`.

---

## 10. Конфигурация / окружение

Переменные (`test.env` и runtime):
- `DATA_PATH` — корень локальных Parquet-данных.
- `ETL_TIMEFRAME` — таймфрейм ETL (`5m`, `1h`, …).
- `TG_BOT_TOKEN`, `TG_CHAT` — Telegram-уведомления (опционально).

Прочее: `.editorconfig` (max line 120), `sonar-project.properties` (SonarQube),
pylint (`max-line-length=120`, `max-args=8`, `max-positional-arguments=6`).

---

## 11. Точки расширения (как дорабатывать)

| Задача | Где менять | Как |
|--------|-----------|-----|
| Добавить новый источник данных | `src/exchange/` | новый класс-наследник `AbstractExchange`, реализовать абстрактные методы; зарегистрировать в фабриках |
| Добавить вычисляемую колонку | `options_lib/enrichment/` + `dictionary/_dataframe_columns.py` | новая функция + запись в `OptionsColumns` и при необходимости в `OPTION_COLUMNS_DEPENDENCIES`; подключить в `OptionEnrichment` |
| Новая аналитика | `options_lib/analytic/` + обёртка в `options_assembler/analytic/` | чистая функция над DataFrame + метод-фасад |
| Новый тип графика | `options_lib/chart/` + `options_assembler/chart/` | подготовка данных + метод рендера |
| Новый ETL-источник | `options_etl/` | наследник `EtlOptions` |
| Канал уведомлений | `messanger/` | наследник `AbstractMessanger` |

**Соглашения кода:**
- Колонки DataFrame — только через enum'ы `OptionsColumns`/`FuturesColumns`, не строки.
- Pydantic-модели для сущностей и параметров запросов.
- Чистая логика (без I/O и состояния) живёт в `options_lib`; состояние и провайдер — в `options_assembler`.
- Линия ≤ 120 символов; для приватных (`_`) и тестовых (`test_`) функций docstring не обязателен.

---

## 12. Известные нюансы / TODO для будущей работы

- Проект на стадии разработки — публичный API нестабилен.
- `pricer/`, `forecast/`, `validation/` в `options_assembler/` — заготовки, требуют наполнения.
- `BinanceExchange` — минимальная реализация.

---

## 13. Быстрый старт для AI-ассистента (Copilot и др.)

1. Источник истины об архитектуре — этот файл + код в `src/`. `CLAUDE.md` — инструкции для Claude Code.
2. Начинать чтение с `src/options_assembler/option_class.py` (фасад) и
   `src/options_lib/dictionary/` (словарь колонок и enum'ов).
3. Перед изменением логики данных смотреть `OPTION_COLUMNS_DEPENDENCIES`.
4. Для новой биржи копировать паттерн `src/exchange/deribit.py`.
5. Тесты обязательны: класть в `tests/unit/<область>/`, использовать существующие fixtures.
6. Проверка: `pytest` и `pylint src/` перед коммитом.
