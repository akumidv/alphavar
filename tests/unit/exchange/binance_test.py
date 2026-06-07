"""Binance exchange provider"""

from alphavar.provider import AbstractProvider
from alphavar.exchange import AbstractExchange
from alphavar.exchange.binance import BinanceExchange


def test_binance_exchange_init():
    binance = BinanceExchange()
    assert isinstance(binance, AbstractExchange)
    assert isinstance(binance, AbstractProvider)
