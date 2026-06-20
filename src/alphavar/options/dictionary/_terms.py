"""Options/futures domain term registry — extends the core vocabulary (R0, R4.3).

Core terms (timestamp, price, iv, asset_code, greeks, …) come from
``alphavar.core.dictionary.Term``. Here we add only the terms specific to the
options/futures domain. ``OptionsTerm`` inherits ``Term``, so ``OptionsTerm.PRICE`` and
``OptionsTerm.STRIKE`` are both available from one place. Each term is used verbatim in every
position (column label, variable, parameter), not just as a column.
"""

from typing import Final

from alphavar.core.dictionary import Term


class OptionsTerm(Term):
    """Options/futures term registry (core terms + domain terms; one name per concept).

    Adds the **derivatives** terms that core (neutral, shared by spot too) must not describe:
    the contract/underlying structure, implied volatility, mark/settlement, greeks, and open
    interest. Spot data simply doesn't carry these — which is exactly what keeping them here,
    not in core, makes explicit (R0 / R4.3)."""

    # --- Derivative contract structure (R4.1.1 / R4.5) ---
    CONTRACT_KIND: Final = "contract_kind"
    """Contract/product kind (``ContractKind``: vanilla / cso / stir / combo …) — same
    asset class, different products. Deribit ``future_combo``/``option_combo`` map here."""

    EXPIRATION_DATE: Final = "expiration_date"
    """Contract expiration date."""

    UNDERLYING_CODE: Final = "underlying_asset_code"
    """Underlying contract code (None for spot)."""

    UNDERLYING_ASSET_CLASS: Final = "underlying_asset_class"
    """Asset class of the underlying (``AssetClass``). Was ``underlying_asset_type``."""

    UNDERLYING_EXPIRATION_DATE: Final = "underlying_expiration_date"
    """Underlying contract expiration date."""

    # --- Implied vol / mark / settlement (R4.2; derivatives) ---
    IV: Final = "iv"
    """Our normalized implied volatility (headline value)."""

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

    OPEN_INTEREST: Final = "open_interest"  # contracts

    # --- Greeks (derivatives) ---
    DELTA: Final = "delta"
    GAMMA: Final = "gamma"
    VEGA: Final = "vega"
    THETA: Final = "theta"
    RHO: Final = "rho"

    # --- Option contract attributes (classification axes: R4.5) ---
    STRIKE: Final = "strike"
    """Option strike price."""

    OPTION_RIGHT: Final = "option_right"
    """Call / put — the option *right* (``OptionRight`` code). NOT ``side`` (buy/sell of a
    position) and NOT ``type`` (overloaded). Was ``option_type``."""

    OPTION_STYLE: Final = "option_style"
    """American / European (``OptionStyle`` code). Changes the pricing model."""

    SERIES_TENOR: Final = "series_tenor"
    """Weekly / monthly / quarterly (``SeriesTenor`` code) — series periodicity."""

    SERIES_CODE: Final = "series_code"
    """Exchange option-series code (MOEX). Equal to ``BASE_CODE`` for spot."""

    # --- Derived / enrichment (R4.3: function add_<x> produces column <x>) ---
    UNDERLYING_PRICE: Final = "underlying_price"
    """Price of the underlying (from the futures/spot join)."""

    INTRINSIC_VALUE: Final = "intrinsic_value"
    """Intrinsic value — produced by ``add_intrinsic_value``."""

    TIMED_VALUE: Final = "timed_value"
    """Time value — produced by ``add_timed_value``."""

    PRICE_STATUS: Final = "price_status"
    """ATM/ITM/OTM (OptionsPriceStatus code) — produced by ``get_price_status``."""


# Dependency graph for enrichment: column -> columns it requires (R4 dictionary).
OPTION_COLUMN_DEPENDENCIES: dict[str, list[str]] = {
    OptionsTerm.INTRINSIC_VALUE: [OptionsTerm.UNDERLYING_PRICE],
    OptionsTerm.TIMED_VALUE: [OptionsTerm.INTRINSIC_VALUE],
    OptionsTerm.PRICE_STATUS: [OptionsTerm.UNDERLYING_PRICE],
}
