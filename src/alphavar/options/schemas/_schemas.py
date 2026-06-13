"""pandera schemas for the options/futures domain (R4.4).

Every field binds to the registry **by reference** (``alias=OptionsCol.X``) — names are
never restated as string literals. Shared column groups are mixin models; entity models
compose mixins + domain fields.

Validation policy (R4.4): ``strict=False`` (extra columns allowed — datasets carry
optional columns), ``coerce=True`` (fix dtypes after parquet/ETL), ``lazy=True`` at call
sites (collect all errors at once). Optional columns use ``typing.Optional[...]`` (when
absent, not validated; when present, checked). Validate at layer boundaries; disable in
production ETL via pandera config.
"""
from typing import Optional

import pandas as pd
import pandera.pandas as pa

from alphavar.core.dictionary import InstrumentKind
from alphavar.options.dictionary import OptionsCol as C, OptionRight, OptionStyle

# Classification columns are category dtype (R4.5: compactness via dtype, not codes);
# their allowed values are the StrEnum members.
_RIGHT_VALUES = [r.value for r in OptionRight]
_KIND_VALUES = [k.value for k in InstrumentKind]
_STYLE_VALUES = [s.value for s in OptionStyle]


class _Base(pa.DataFrameModel):
    class Config:
        strict = False      # extra/optional columns allowed
        coerce = True       # coerce dtypes (parquet/ETL hygiene)


# --- Mixins: shared column groups, each name declared once ---

class TimestampMixin(_Base):
    timestamp: pd.Timestamp = pa.Field(alias=C.TIMESTAMP)


class QuoteMixin(_Base):
    price: float = pa.Field(alias=C.PRICE, nullable=True)
    ask: Optional[float] = pa.Field(alias=C.ASK, nullable=True)
    bid: Optional[float] = pa.Field(alias=C.BID, nullable=True)


class OHLCMixin(_Base):
    open: Optional[float] = pa.Field(alias=C.OPEN, nullable=True)
    high: Optional[float] = pa.Field(alias=C.HIGH, nullable=True)
    low: Optional[float] = pa.Field(alias=C.LOW, nullable=True)
    close: Optional[float] = pa.Field(alias=C.CLOSE, nullable=True)


class GreeksMixin(_Base):
    iv: Optional[float] = pa.Field(alias=C.IV, nullable=True)
    delta: Optional[float] = pa.Field(alias=C.DELTA, nullable=True)
    gamma: Optional[float] = pa.Field(alias=C.GAMMA, nullable=True)
    vega: Optional[float] = pa.Field(alias=C.VEGA, nullable=True)
    theta: Optional[float] = pa.Field(alias=C.THETA, nullable=True)
    rho: Optional[float] = pa.Field(alias=C.RHO, nullable=True)


class IdentityMixin(_Base):
    """Two-level identity (R4.1.1) + instrument kind (R4.5). `asset_code` is the
    underlying key; `exch_symbol` is the optional raw venue ticker."""
    asset_code: str = pa.Field(alias=C.ASSET_CODE)
    instrument_kind: pd.CategoricalDtype = pa.Field(
        alias=C.INSTRUMENT_KIND, dtype_kwargs={"categories": _KIND_VALUES, "ordered": False},
        isin=_KIND_VALUES,
    )
    exch_symbol: Optional[str] = pa.Field(alias=C.EXCH_SYMBOL, nullable=True)


# --- Entity models: mandatory row key (R4.1.1) + composed mixins ---

class OptionsHistory(IdentityMixin, TimestampMixin, QuoteMixin, OHLCMixin, GreeksMixin):
    """Parsed options history. Mandatory key (R4.1.1):
    (asset_code, expiration_date, strike, option_right, timestamp)."""
    expiration_date: pd.Timestamp = pa.Field(alias=C.EXPIRATION_DATE)
    strike: float = pa.Field(alias=C.STRIKE, gt=0)
    # Classification axes (R4.5): category dtype, values restricted to the StrEnum.
    option_right: pd.CategoricalDtype = pa.Field(
        alias=C.OPTION_RIGHT, dtype_kwargs={"categories": _RIGHT_VALUES, "ordered": False},
        isin=_RIGHT_VALUES,
    )
    option_style: Optional[str] = pa.Field(alias=C.OPTION_STYLE, isin=_STYLE_VALUES, nullable=True)


class FuturesHistory(IdentityMixin, TimestampMixin, QuoteMixin, OHLCMixin):
    """Parsed futures history. Mandatory key: (asset_code, expiration_date, timestamp)."""
    expiration_date: pd.Timestamp = pa.Field(alias=C.EXPIRATION_DATE, nullable=True)


class SpotHistory(IdentityMixin, TimestampMixin, QuoteMixin, OHLCMixin):
    """Parsed spot history. Mandatory key: (asset_code, timestamp)."""
