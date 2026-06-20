"""
Abstract class with mandatory interfaces for every provider

Provider limits:
- provide data if it has it. For example if exchange provider do not support history it will not return option_history
- if local files do not contain chain it will not return data
- if request is wrong - for example there is not option for expiration_date it throw an error
It is not planned that provider level will be contained any data logic. It should be in option data class
"""

import datetime
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from alphavar.core.dictionary import InstrumentKind
from alphavar.io.provider._provider_entities import RequestParameters
from alphavar.options.dictionary import OptionsTerm, Timeframe
from alphavar.options.entities import AssetMeta


class AbstractProvider(ABC):
    """Provider interfaces"""

    exchange_code: str
    options_columns: list = [
        OptionsTerm.TIMESTAMP,
        OptionsTerm.STRIKE,
        OptionsTerm.EXPIRATION_DATE,
        OptionsTerm.OPTION_RIGHT,
        OptionsTerm.PRICE,
        OptionsTerm.UNDERLYING_EXPIRATION_DATE,
        OptionsTerm.UNDERLYING_PRICE,
    ]
    futures_columns: list = [
        OptionsTerm.TIMESTAMP,
        OptionsTerm.EXPIRATION_DATE,
        OptionsTerm.PRICE,
    ]

    def __init__(self, exchange_code: str, **kwargs: Any) -> None:
        self.exchange_code = exchange_code
        super().__init__(**kwargs)

    def load_reference(self, asset_code: str) -> tuple[AssetMeta | None, pd.DataFrame]:
        """Per-asset reference layer (R4.6, T25): asset-level ``AssetMeta`` + the contract-level
        SCD-2 history. Default: no reference — ``(None, empty frame)``. File providers that store
        a reference beside the time series override this; exchange/live providers do not have one.
        """
        return None, pd.DataFrame()

    @abstractmethod
    def get_assets_list(self, asset_kind: InstrumentKind) -> list[str]:
        """List of symbols"""

    @abstractmethod
    def get_asset_history_years(self, asset_code: str, asset_kind: InstrumentKind, timeframe: Timeframe) -> list[int]:
        """List of history years"""

    @abstractmethod
    def load_options_history(
        self,
        asset_code: str,
        params: RequestParameters,
        columns: list | None = None,
    ) -> pd.DataFrame:
        """Provide options by period, timeframe"""

    @abstractmethod
    def load_options_book(
        self,
        asset_code: str,
        settlement_datetime: datetime.datetime | None = None,
        timeframe: Timeframe = Timeframe.EOD,
        columns: list | None = None,
    ) -> pd.DataFrame:
        """Provide options for datetime, timeframe"""

    @abstractmethod
    def load_futures_history(
        self,
        asset_code: str,
        params: RequestParameters,
        columns: list | None = None,
    ) -> pd.DataFrame:
        """Provide future by period, timeframe"""

    @abstractmethod
    def load_futures_book(
        self,
        asset_code: str,
        settlement_datetime: datetime.datetime | None = None,
        timeframe: Timeframe = Timeframe.EOD,
        columns: list | None = None,
    ) -> pd.DataFrame:
        """Provide futures for datetime, timeframe"""

    @abstractmethod
    def load_options_chain(
        self,
        asset_code: str,
        settlement_datetime: datetime.datetime | None = None,
        expiration_date: datetime.datetime | None = None,
        timeframe: Timeframe = Timeframe.EOD,
        columns: list | None = None,
    ) -> pd.DataFrame | None:
        """Provide options chain by request to api if supported. Otherwise, return None"""
