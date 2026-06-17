"""Options/futures domain dictionary (extends core registry) + domain axes (R4.5).

Hosts both the v2 plain-string registry (``OptionsCol`` + classification ``StrEnum``
axes) and the legacy v1 column enums (``OptionsColumns`` etc.), which still run in
parallel until the T23.1 migration drops them.
"""
from alphavar.options.dictionary._columns import OptionsCol, OPTION_COLUMN_DEPENDENCIES
from alphavar.options.dictionary._classification import (
    OptionRight, OptionStyle, OptionPriceStatus, SeriesTenor,
)

# Legacy v1 dictionary (parallel to the v2 registry until T23.1 lands).
from alphavar.options.dictionary.enum_code import EnumCode, EnumDataFrameColumn, EnumMultiplier
from alphavar.options.dictionary._timeframe_types import Timeframe
from alphavar.options.dictionary._asset_types import AssetType
from alphavar.options.dictionary._options_types import OptionsType, OptionsPriceStatus, OptionsStyle
from alphavar.options.dictionary._dataframe_columns import (
    OptionsColumns, FuturesColumns, SpotColumns,
    OPTION_COLUMNS_DEPENDENCIES, OPTION_NON_FUTURES_COLUMN_NAMES, OPTION_NON_SPOT_COLUMN_NAMES,
    ALL_COLUMN_NAMES,
)
from alphavar.options.dictionary._options_leg import LegType
from alphavar.options.dictionary._currency import Currency

__all__ = [
    # v2 registry + axes
    "OptionsCol", "OPTION_COLUMN_DEPENDENCIES",
    "OptionRight", "OptionStyle", "OptionPriceStatus", "SeriesTenor",
    # legacy v1
    "EnumCode", "EnumDataFrameColumn", "EnumMultiplier", "Timeframe", "AssetType",
    "OptionsType", "OptionsPriceStatus", "OptionsStyle",
    "OptionsColumns", "FuturesColumns", "SpotColumns",
    "OPTION_COLUMNS_DEPENDENCIES", "OPTION_NON_FUTURES_COLUMN_NAMES",
    "OPTION_NON_SPOT_COLUMN_NAMES", "ALL_COLUMN_NAMES", "LegType", "Currency",
]
