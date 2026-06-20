"""Binance exchange provider"""

from alphavar.io.exchange import AbstractExchange
from alphavar.io.exchange.binance import BinanceExchange
from alphavar.io.provider import AbstractProvider


def test_binance_exchange_init():
    binance = BinanceExchange()
    assert isinstance(binance, AbstractExchange)
    assert isinstance(binance, AbstractProvider)
