""" "Public price analytic api class that should hide realization of functions"""

import pandas as pd

from alphavar.options.dictionary import OptionsTerm, OptionsType
from alphavar.options.enrichment_class import OptionsEnrichment
from alphavar.options.lib.analytic.price._time_values import (
    time_value_series_by_atm_distance,
    time_value_series_by_strike_to_atm_distance,
)
from alphavar.options.option_data_class import OptionsData


class OptionsAnalyticPrice:
    """
    Wrapper about price analytics modules functions
    """

    def __init__(self, data: OptionsData):
        self._data = data
        self._enrichment: OptionsEnrichment = OptionsEnrichment(self._data)

    def time_value_series_by_strike_to_atm_distance(
        self,
        strike: float | None = None,
        expiration_date: pd.Timestamp | None = None,
        option_type: OptionsType | None = OptionsType.CALL,
    ) -> pd.DataFrame:
        """Get time value series by strike to atm distance"""
        self._enrichment.enrich_options([OptionsTerm.INTRINSIC_VALUE, OptionsTerm.TIMED_VALUE])
        return time_value_series_by_strike_to_atm_distance(self._data.df_hist, strike, expiration_date, option_type)

    def time_value_series_by_atm_distance(
        self,
        distance: float | None = None,
        expiration_date: pd.Timestamp | None = None,
        option_type: OptionsType | None = OptionsType.CALL,
    ) -> pd.DataFrame:
        """Get time value series by distance from atm"""
        self._enrichment.enrich_options([OptionsTerm.INTRINSIC_VALUE, OptionsTerm.TIMED_VALUE])
        return time_value_series_by_atm_distance(self._data.df_hist, distance, expiration_date, option_type)
