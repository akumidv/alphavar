"""Core term registry — the domain-neutral vocabulary of data concepts (R4.3).

The single source of truth for the canonical *name of a data concept* that is not specific
to one asset class. A concept has exactly one term here, used **verbatim in every position**
— as a DataFrame column label, as a variable/parameter name in the functions that compute or
modify that data, and in ``add_<x>``/``get_<x>`` accessors. The point is one shared word per
concept so the codebase has a single understanding of each term (a column is only one of its
uses, not its definition).

Values are **plain strings** (R4.3): a member of ``Term`` *is* the term's string, so it needs
no ``.nm`` accessor and never has to be normalized before ``to_parquet``. The registry is
**engine-neutral** — it carries no pandas/polars dtypes (those live in the schema layer,
R4.4 / R8).

Domain-specific terms (strike, option_right, …) extend this in the domain dictionary
(e.g. ``alphavar.options.dictionary``), per R0 "core + domain extensions".
"""

from typing import Final


class Term:
    """Registry of domain-neutral data terms (one canonical name per concept, R4.3).

    Reference as ``Term.PRICE`` (resolves to ``"price"``). Use it everywhere the concept
    appears — column label, variable, parameter — never the bare string literal.
    """

    # --- Identity (R4.1.1: two-level model) ---
    ASSET_CODE: Final = "asset_code"
    """Underlying asset code (BRN, BTC, AAPL). Unifying key across a future and an
    option on the same asset. Exchange-neutral, short, stable; usable in file paths.
    Present on every row."""

    EXCH_SYMBOL: Final = "exch_symbol"
    """Exchange instrument symbol — the venue's raw contract ticker
    (BTC-30APR25-100000-C, BR-3.25). Optional in parsed data (R4.1.1); ``exch_`` prefix
    marks it as raw venue data."""

    # --- Classification axes (R4.4: kind vs class vs right vs style — distinct axes) ---
    INSTRUMENT_KIND: Final = "instrument_kind"
    """Instrument kind (``InstrumentKind``: options / futures / spot) — the *form* of the
    traded instrument. Was the mislabeled ``asset_type`` (which held a kind, not a type).
    A column on every row."""

    ASSET_CLASS: Final = "asset_class"
    """Underlying asset class (``AssetClass``: equity / commodity / crypto / index /
    currency) — the *nature of the underlying*. A property of ``asset_code`` (one asset →
    one class). Was the mislabeled ``AssetType`` enum."""

    CONTRACT_KIND: Final = "contract_kind"
    """Contract/product kind (``ContractKind``: vanilla / cso / stir / combo …) — same
    asset class, different products/trading. Deribit ``future_combo``/``option_combo``
    map here."""

    BASE_CODE: Final = "base_asset_code"
    """Base sub-asset code. Equals ASSET_CODE for spot."""

    UNDERLYING_CODE: Final = "underlying_asset_code"
    """Underlying contract code (None for spot)."""

    UNDERLYING_ASSET_CLASS: Final = "underlying_asset_class"
    """Asset class of the underlying (``AssetClass``). Was ``underlying_asset_type``."""

    CURRENCY: Final = "currency"
    """Settlement/quote currency code."""

    TITLE: Final = "title"
    """Human-readable instrument title."""

    # --- Time (R4.2: ours vs venue) ---
    TIMESTAMP: Final = "timestamp"
    """Our normalized instant the library uses (rounded). Ours — no prefix."""

    REQUEST_TIMESTAMP: Final = "request_timestamp"
    """When we fetched the snapshot. Ours."""

    EXCH_TIMESTAMP: Final = "exch_timestamp"
    """The venue's own timestamp on the record (Deribit creation, MOEX update). Raw
    venue data — ``exch_`` prefix. Renamed from the old ``original_timestamp``."""

    EXPIRATION_DATE: Final = "expiration_date"
    """Contract expiration date."""

    UNDERLYING_EXPIRATION_DATE: Final = "underlying_expiration_date"
    """Underlying contract expiration date."""

    # --- Reference validity (R4.6: SCD Type 2 on reference records) ---
    VALID_FROM: Final = "valid_from"
    """Inclusive start of a reference record's validity (SCD Type 2)."""

    VALID_TO: Final = "valid_to"
    """Exclusive end of a reference record's validity; NaT = still open (current)."""

    # --- Price / IV (R4.2) ---
    PRICE: Final = "price"
    """Our normalized price (BS + smile fit + no-arbitrage) — the library's headline
    value. NOT a copy of bid/ask/mid."""

    IV: Final = "iv"
    """Our normalized implied volatility (headline value)."""

    EXCH_PRICE: Final = "exch_price"
    """Exchange traded/quoted price as received (raw venue data)."""

    EXCH_IV: Final = "exch_iv"
    """Exchange-published implied volatility (raw venue data)."""

    EXCH_MARK_PRICE: Final = "exch_mark_price"
    """Exchange mark / fair-value estimate (Deribit mark_price, MOEX theorprice).
    An estimate, not a trade."""

    EXCH_MARK_IV: Final = "exch_mark_iv"
    """Exchange mark implied volatility."""

    SETTLE_PRICE: Final = "settle_price"
    """Official daily clearing/settlement price. EOD-only; null intraday."""

    SETTLE_IV: Final = "settle_iv"
    """Settlement implied volatility. EOD-only."""

    # --- Quotes / volumes ---
    ASK: Final = "ask"
    BID: Final = "bid"
    LAST: Final = "last"
    OPEN_INTEREST: Final = "open_interest"  # contracts
    VOLUME: Final = "volume"  # contracts
    VOLUME_PREMIUM: Final = "volume_premium"  # money
    VOLUME_NOTIONAL: Final = "volume_notional"  # money
    HIGH_24: Final = "high_24"
    LOW_24: Final = "low_24"

    # --- OHLC ---
    OPEN: Final = "open"
    CLOSE: Final = "close"
    HIGH: Final = "high"
    LOW: Final = "low"

    # --- Greeks ---
    DELTA: Final = "delta"
    GAMMA: Final = "gamma"
    VEGA: Final = "vega"
    THETA: Final = "theta"
    RHO: Final = "rho"
