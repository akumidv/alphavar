"""Domain-neutral classification axes (R4.5).

Each axis is an independent ``StrEnum``; values stored in per-row columns are the
**singular human value** (one row = one contract), matching exchange APIs
(Deribit ``kind="option"``). Storage compactness comes from the **category dtype**
declared in the schema layer (R4.4), not from a hand-rolled short code — so there is no
``.code``/``.value`` duality and raw data stays readable.

``StrEnum`` members *are* ``str``, so ``df[Term.OPTION_RIGHT] == OptionRight.CALL`` works
directly without ``.value``.
"""

import enum


@enum.unique
class InstrumentKind(enum.StrEnum):
    """The *form* of the traded instrument (column ``instrument_kind``).

    Singular values, like Deribit's ``kind``. Replaces the mislabeled ``AssetKind`` /
    ``asset_type`` (which stored plural ``options``/``futures``).
    """

    OPTION = "option"
    FUTURE = "future"
    SPOT = "spot"


@enum.unique
class AssetClass(enum.StrEnum):
    """The nature of the *underlying* asset (column ``asset_class``).

    A property of ``asset_code`` (one asset → one class). Replaces the mislabeled
    ``AssetType`` enum (``SHARE`` → ``EQUITY``).
    """

    EQUITY = "equity"
    COMMODITY = "commodity"
    INDEX = "index"
    CURRENCY = "currency"
    CRYPTO = "crypto"


@enum.unique
class ContractKind(enum.StrEnum):
    """Contract/product kind (column ``contract_kind``): same asset class, different
    product or trading. Deribit ``future_combo``/``option_combo`` map to ``COMBO``.
    """

    VANILLA = "vanilla"
    COMBO = "combo"
    CSO = "cso"  # calendar spread option
    STIR = "stir"  # short-term interest rate
