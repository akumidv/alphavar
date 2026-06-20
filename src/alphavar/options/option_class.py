"""Ralisation for option class"""

import datetime

import pandas as pd

from alphavar.io.provider import AbstractProvider, RequestParameters
from alphavar.options.analytic_class import OptionsAnalytic
from alphavar.options.chain_class import OptionsChain
from alphavar.options.chart_class import ChartClass
from alphavar.options.dictionary import Timeframe
from alphavar.options.enrichment_class import OptionsEnrichment
from alphavar.options.option_data_class import OptionsData
from alphavar.options.pricer_class import OptionsPricer


class Option:
    """Base option class that provide possibility to work with option data different way"""

    _data: OptionsData

    def __init__(
        self,
        provider: AbstractProvider,
        asset_code: str,
        params: RequestParameters | None = None,
        option_columns: list | None = None,
        future_columns: list | None = None,
    ):
        self._data = OptionsData(provider, asset_code, params, option_columns, future_columns)
        self.enrichment: OptionsEnrichment = OptionsEnrichment(self._data)
        self.chain: OptionsChain = OptionsChain(self._data)
        self.analytic: OptionsAnalytic = OptionsAnalytic(self._data)
        self.chart: ChartClass = ChartClass(self._data)
        self.pricer: OptionsPricer = OptionsPricer(self._data)

    @property
    def asset_code(self) -> str:
        """Underlying asset code"""
        return self._data.asset_code

    @property
    def reference(self):
        """Asset-level reference metadata (``AssetMeta``) for this asset, or ``None`` when the
        stored data has no reference layer yet (R4.6, T25)."""
        return self._data.reference

    @property
    def period_from(self) -> int | datetime.date | datetime.datetime | None:
        """Option data period from"""
        return self._data.period_from

    @property
    def period_to(self) -> int | datetime.date | datetime.datetime | None:
        """Option data period to"""
        return self._data.period_to

    @property
    def timeframe(self) -> Timeframe:
        """Option data timeframe"""
        return self._data.timeframe

    @property
    def df_hist(self):
        """Option dataframe getter"""
        return self._data.df_hist

    @df_hist.setter
    def df_hist(self, df: pd.DataFrame):
        """Option dataframe setter"""
        self._data.df_hist = df

    @property
    def df_fut(self) -> pd.DataFrame:
        """Future dataframe getter"""
        return self._data.df_fut

    @df_fut.setter
    def df_fut(self, df: pd.DataFrame):
        """Future dataframe setter"""
        self._data.df_fut = df
