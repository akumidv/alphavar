"""Binance exchange provider"""

from alphavar.io.provider import AbstractProvider
from alphavar.io.exchange import AbstractExchange
from alphavar.io.exchange.binance import BinanceExchange


def test_binance_exchange_init():
    binance = BinanceExchange()
    assert isinstance(binance, AbstractExchange)
    assert isinstance(binance, AbstractProvider)
