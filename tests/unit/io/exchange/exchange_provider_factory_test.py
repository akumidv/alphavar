"""Provider fabric tests"""
from alphavar.io.provider import DataSource, DataEngine
from alphavar.io.provider import (
    PandasLocalFileProvider
)
from alphavar.io.exchange import ExchangeCode
from alphavar.io.exchange import BinanceExchange, DeribitExchange, get_provider


def test_get_provider_local(exchange_code, data_path):
    provider = get_provider(exchange_code, storage=DataSource.LOCAL, data_path=data_path)
    assert isinstance(provider, PandasLocalFileProvider)


def test_get_provider_exchange_binance():
    provider = get_provider(ExchangeCode.BINANCE.value, storage=DataSource.API, engine=DataEngine.PANDAS)
    assert isinstance(provider, BinanceExchange)


def test_get_provider_exchange_deribit():
    provider = get_provider(ExchangeCode.DERIBIT.value, storage=DataSource.API, engine=DataEngine.PANDAS)
    assert isinstance(provider, DeribitExchange)
