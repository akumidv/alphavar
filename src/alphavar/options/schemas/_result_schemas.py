"""Result-chain interchange schemas (A4a / D-b) — the pinned tidy form of a producer's output.

Distinct from the market-data entity schemas (``_schemas.py``: ``OptionsHistory`` …): these pin the
**interchange** frames passed between capability areas (the result-chain). V1 covers the price
slice — ``price_series`` and ``forecast_distribution``; the full Shape-2 catalog is design point D-b.

Columns bind to the registry by reference (``alias=...``): market-data terms via ``Term`` (series
``timestamp``/``price``), result terms via ``ResultTerm`` (``quantile``/``value``/``change``). Same
validation policy as the entity schemas (``strict=False``, ``coerce=True``, ``lazy=True`` at call).
"""

import pandas as pd
import pandera.pandas as pa

from alphavar.core.dictionary import ResultTerm, Term


class _Base(pa.DataFrameModel):
    class Config:
        strict = False  # extra columns allowed
        coerce = True  # coerce dtypes (interchange hygiene)


class PriceSeriesSchema(_Base):
    """A ``price_series`` interchange frame: one positive price per timestamp, chronological."""

    timestamp: pd.Timestamp = pa.Field(alias=Term.TIMESTAMP, nullable=False)
    price: float = pa.Field(alias=Term.PRICE, gt=0, nullable=False)


class ForecastDistributionSchema(_Base):
    """A ``forecast_distribution`` interchange frame: one row per quantile of the terminal value.

    ``change = value − spot`` (the spot scalar rides on the result object / contract scalar-spec).
    """

    quantile: float = pa.Field(alias=ResultTerm.QUANTILE, gt=0, lt=1, nullable=False)
    value: float = pa.Field(alias=ResultTerm.VALUE, nullable=False)
    change: float = pa.Field(alias=ResultTerm.CHANGE, nullable=False)


class SmileForecastSchema(_Base):
    """A ``forecast_smile`` interchange frame: expected σ(k) per log-moneyness (+ quantile bands).

    Pins the fixed columns; the per-quantile ``iv_q*`` bands are extra (``strict=False``).
    """

    k: float = pa.Field(nullable=False)
    iv: float = pa.Field(ge=0, nullable=False)


class SurfaceForecastSchema(_Base):
    """A ``forecast_surface`` interchange frame: expected σ(k,τ) per ``(tenor, k)`` (+ quantile bands)."""

    tenor: float = pa.Field(gt=0, nullable=False)
    k: float = pa.Field(nullable=False)
    iv: float = pa.Field(ge=0, nullable=False)
