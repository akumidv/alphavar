"""Options-domain classification axes (R4.5).

Domain-specific axes that extend the neutral core axes. ``StrEnum`` with singular human
values; compactness is the schema's category dtype (R4.4), not a hand-rolled code.
"""

import enum


@enum.unique
class OptionRight(enum.StrEnum):
    """The option *right* (column ``option_right``): call or put.

    NOT ``side`` (buy/sell of a position) and NOT ``type`` (overloaded). Replaces
    ``OptionsType``.
    """

    CALL = "call"
    PUT = "put"


@enum.unique
class OptionStyle(enum.StrEnum):
    """Exercise style (column ``option_style``): changes the pricing model."""

    AMERICAN = "american"
    EUROPEAN = "european"


@enum.unique
class OptionPriceStatus(enum.StrEnum):
    """Moneyness (column ``price_status``): at / in / out of the money."""

    ATM = "atm"
    ITM = "itm"
    OTM = "otm"


@enum.unique
class SeriesTenor(enum.StrEnum):
    """Series periodicity (column ``series_tenor``): separate trading series."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@enum.unique
class ContractKind(enum.StrEnum):
    """Contract/product kind (column ``contract_kind``): same asset class, different
    product or trading. Deribit ``future_combo``/``option_combo`` map to ``COMBO``.

    Derivatives-domain axis (lives with options, not core): a spot row has no contract
    kind, and any future spot product would define its own values.
    """

    VANILLA = "vanilla"
    COMBO = "combo"
    CSO = "cso"  # calendar spread option
    STIR = "stir"  # short-term interest rate
