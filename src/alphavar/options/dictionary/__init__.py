"""Options/futures domain dictionary (extends core registry) + domain axes (R4.5).

The term vocabulary is the v2 plain-string registry (``OptionsTerm`` + classification
``StrEnum`` axes; one canonical name per concept, used as column / variable / parameter);
per-dataset membership lives in ``_column_sets``. The old
``OptionsColumns``/``FuturesColumns``/``SpotColumns`` enums were dropped (T23.1).
"""

from alphavar.options.dictionary._asset_types import AssetType
from alphavar.options.dictionary._classification import (
    ContractKind,
    OptionPriceStatus,
    OptionRight,
    OptionStyle,
    SeriesTenor,
)
from alphavar.options.dictionary._column_sets import (
    ALL_COLUMN_NAMES,
    FUTURES_COLUMN_NAMES,
    OPTION_NON_FUTURES_COLUMN_NAMES,
    OPTION_NON_SPOT_COLUMN_NAMES,
    OPTIONS_COLUMN_NAMES,
    SPOT_COLUMN_NAMES,
)
from alphavar.options.dictionary._currency import Currency
from alphavar.options.dictionary._options_leg import LegType
from alphavar.options.dictionary._options_types import OptionsPriceStatus, OptionsStyle, OptionsType
from alphavar.options.dictionary._terms import OPTION_COLUMN_DEPENDENCIES, OptionsTerm
from alphavar.options.dictionary._timeframe_types import Timeframe
from alphavar.options.dictionary.enum_code import EnumCode, EnumDataFrameColumn, EnumMultiplier

__all__ = [
    # column registry + per-dataset membership
    "OptionsTerm",
    "OPTION_COLUMN_DEPENDENCIES",
    "OPTIONS_COLUMN_NAMES",
    "FUTURES_COLUMN_NAMES",
    "SPOT_COLUMN_NAMES",
    "OPTION_NON_FUTURES_COLUMN_NAMES",
    "OPTION_NON_SPOT_COLUMN_NAMES",
    "ALL_COLUMN_NAMES",
    # classification axes
    "OptionRight",
    "OptionStyle",
    "OptionPriceStatus",
    "SeriesTenor",
    "ContractKind",
    # enums / scalars
    "EnumCode",
    "EnumDataFrameColumn",
    "EnumMultiplier",
    "Timeframe",
    "AssetType",
    "OptionsType",
    "OptionsPriceStatus",
    "OptionsStyle",
    "LegType",
    "Currency",
]
