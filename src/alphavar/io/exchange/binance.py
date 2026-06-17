"""
Binance api provider
"""
import datetime
import pandas as pd

from alphavar.options.dictionary import Timeframe
from alphavar.core.dictionary import InstrumentKind
from alphavar.io.provider import DataEngine, RequestParameters
from alphavar.io.exchange.exchange_entities import ExchangeCode
from alphavar.io.exchange._abstract_exchange import AbstractExchange, BookData


class BinanceExchange(AbstractExchange):
    """Binance exchange api"""
    API_URL = 'https://api.binance.com'

    def load_futures_book(self, asset_code: str, settlement_datetime: datetime.datetime | None = None,
                         timeframe: Timeframe = Timeframe.EOD, columns: list | None = None) -> pd.DataFrame:
        raise NotImplementedError

    def load_options_book(self, asset_code: str, settlement_datetime: datetime.datetime | None = None,
                         timeframe: Timeframe = Timeframe.EOD, columns: list | None = None) -> pd.DataFrame:
        raise NotImplementedError

    def get_assets_list(self, asset_kind: InstrumentKind) -> list[str]:
        raise NotImplementedError

    def get_asset_history_years(self, asset_code: str, asset_kind: InstrumentKind,
                                timeframe: Timeframe) -> list[int]:
        """Exchange API does not provide per-year history."""
        raise NotImplementedError

    def get_options_assets_books_snapshot(self, asset_codes: list[str] | str | None = None) -> pd.DataFrame:
        pass

    def __init__(self, engine: DataEngine = DataEngine.PANDAS):
        """"""
        super().__init__(engine, ExchangeCode.BINANCE.name, self.API_URL)

    def load_options_history(self, asset_code: str, params: RequestParameters | None = None,
                            columns: list | None = None) -> pd.DataFrame:
        """load options history"""
        raise NotImplementedError

    def load_futures_history(self, asset_code: str, params: RequestParameters | None = None,
                            columns: list | None = None) -> pd.DataFrame:
        """load futures history"""

    def load_options_chain(self, asset_code: str, settlement_datetime: datetime.datetime | None = None,
                          expiration_date: datetime.datetime | None = None,
                          timeframe: Timeframe = Timeframe.EOD,
                          columns: list | None = None) -> pd.DataFrame | None:
        """Providing option chain by local file system is not supported return None"""
