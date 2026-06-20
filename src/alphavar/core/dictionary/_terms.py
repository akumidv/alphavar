"""Core term registry — the domain-neutral vocabulary of data concepts (R4.3).

The single source of truth for the canonical *name of a data concept* that is shared across
**every** asset domain (spot, futures, options, bonds …). A concept has exactly one term here,
used **verbatim in every position** — as a DataFrame column label, as a variable/parameter name
in the functions that compute or modify that data, and in ``add_<x>``/``get_<x>`` accessors. The
point is one shared word per concept so the codebase has a single understanding of each term (a
column is only one of its uses, not its definition).

This registry holds **only** what is common to all domains: identity, time, the SCD validity
window, the headline/venue price, quotes, volumes and OHLC. Domain-specific terms (derivatives:
expiration, the underlying link, implied vol, greeks, mark/settlement; equities: dividends; …)
live in that domain's dictionary and extend this one — so core never describes one domain's
concepts, and what a domain *adds* shows exactly where two domains' data do and don't line up
(R0 "core + domain extensions").

Values are **plain strings** (R4.3): a member of ``Term`` *is* the term's string, so it needs
no ``.nm`` accessor and never has to be normalized before ``to_parquet``. The registry is
**engine-neutral** — it carries no pandas/polars dtypes (those live in the schema layer,
R4.4 / R8).
"""

from typing import Final


class Term:
    """Registry of domain-neutral data terms (one canonical name per concept, R4.3).

    Reference as ``Term.PRICE`` (resolves to ``"price"``). Use it everywhere the concept
    appears — column label, variable, parameter — never the bare string literal. Domain
    registries (e.g. ``OptionsTerm``) inherit this and add their own terms.
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

    # --- Classification axes (R4.4: kind vs class — distinct axes) ---
    INSTRUMENT_KIND: Final = "instrument_kind"
    """Instrument kind (``InstrumentKind``: option / future / spot) — the *form* of the
    traded instrument; the cross-domain discriminator. A column on every row."""

    ASSET_CLASS: Final = "asset_class"
    """Underlying asset class (``AssetClass``: equity / commodity / crypto / index /
    currency) — the *nature of the underlying*. A property of ``asset_code`` (one asset →
    one class)."""

    BASE_CODE: Final = "base_asset_code"
    """Base sub-asset code. Equals ASSET_CODE for spot."""

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

    # --- Reference validity (R4.6: SCD Type 2 on reference records) ---
    VALID_FROM: Final = "valid_from"
    """Inclusive start of a reference record's validity (SCD Type 2)."""

    VALID_TO: Final = "valid_to"
    """Exclusive end of a reference record's validity; NaT = still open (current)."""

    # --- Price (R4.2) ---
    PRICE: Final = "price"
    """Our normalized price — the library's headline value. NOT a copy of bid/ask/mid."""

    EXCH_PRICE: Final = "exch_price"
    """Exchange traded/quoted price as received (raw venue data)."""

    # --- Quotes / volumes ---
    ASK: Final = "ask"
    BID: Final = "bid"
    LAST: Final = "last"
    VOLUME: Final = "volume"  # contracts/units
    VOLUME_PREMIUM: Final = "volume_premium"  # money
    VOLUME_NOTIONAL: Final = "volume_notional"  # money
    HIGH_24: Final = "high_24"
    LOW_24: Final = "low_24"

    # --- OHLC ---
    OPEN: Final = "open"
    CLOSE: Final = "close"
    HIGH: Final = "high"
    LOW: Final = "low"
