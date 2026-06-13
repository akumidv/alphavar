"""Options/futures domain column registry — extends the core registry (R0, R4.3).

Core names (timestamp, price, iv, asset_code, greeks, …) come from
``alphavar.core.dictionary.Col``. Here we add only the names specific to the
options/futures domain. ``OptionsCol`` inherits ``Col``, so ``OptionsCol.PRICE`` and
``OptionsCol.STRIKE`` are both available from one place.
"""
from typing import Final

from alphavar.core.dictionary import Col


class OptionsCol(Col):
    """Options/futures column registry (core names + domain names)."""

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

    # --- Derived / enrichment (R4.3: function add_<x> produces column <x>) ---
    UNDERLYING_PRICE: Final = "underlying_price"
    """Price of the underlying (from the futures/spot join)."""

    INTRINSIC_VALUE: Final = "intrinsic_value"
    """Intrinsic value — produced by ``add_intrinsic_value``."""

    TIMED_VALUE: Final = "timed_value"
    """Time value — produced by ``add_timed_value``."""

    PRICE_STATUS: Final = "price_status"
    """ATM/ITM/OTM (OptionsPriceStatus code) — produced by ``get_price_status``."""


# Dependency graph for enrichment: column -> columns it requires (R4 / dictionary v2).
OPTION_COLUMN_DEPENDENCIES: dict[str, list[str]] = {
    OptionsCol.INTRINSIC_VALUE: [OptionsCol.UNDERLYING_PRICE],
    OptionsCol.TIMED_VALUE: [OptionsCol.INTRINSIC_VALUE],
    OptionsCol.PRICE_STATUS: [OptionsCol.UNDERLYING_PRICE],
}
