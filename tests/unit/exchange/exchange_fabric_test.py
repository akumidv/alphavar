"""Exchange fabric tests"""
from alphavar.exchange.exchange_entities import ExchangeCode
from alphavar.provider import DataEngine
from alphavar.exchange import (
    get_exchange, DeribitExchange, BinanceExchange
)


def test_get_exchange_binance():
    exchange_provider = get_exchange(ExchangeCode.BINANCE.value)
    assert isinstance(exchange_provider, BinanceExchange)
    assert not isinstance(exchange_provider, DeribitExchange)


def test_get_exchange_deribit():
    exchange_provider = get_exchange(ExchangeCode.DERIBIT.value, engine=DataEngine.PANDAS)
    assert isinstance(exchange_provider, DeribitExchange)
    assert not isinstance(exchange_provider, BinanceExchange)
