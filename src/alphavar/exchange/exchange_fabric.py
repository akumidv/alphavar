"""Fabric to choose exchange by it name"""

from typing import Dict, Type
from alphavar.provider import DataEngine
from alphavar.exchange._abstract_exchange import AbstractExchange
from alphavar.exchange.exchange_entities import ExchangeCode
from alphavar.exchange.binance import BinanceExchange
from alphavar.exchange.deribit import DeribitExchange
from alphavar.exchange.moex import MoexExchange


_EXCHANGES: Dict[ExchangeCode, Type[AbstractExchange]] = {
    ExchangeCode.BINANCE: BinanceExchange,
    ExchangeCode.DERIBIT: DeribitExchange,
    ExchangeCode.MOEX: MoexExchange
}


def get_exchange(exchange_code: str, engine: DataEngine=DataEngine.PANDAS, **kwargs) -> AbstractExchange:
    """Fabric"""
    exchange = ExchangeCode(exchange_code)

    return _EXCHANGES[exchange](engine, **kwargs)


def get_exchange_class(exchange_code) -> Type[AbstractExchange]:
    """Resolve the exchange *class* (no instantiation, no network) — used for class-level
    metadata such as the venue->canonical kind map (``resolve_instrument_kind``).
    Accepts an ``ExchangeCode``, its value (``'deribit'``) or its name (``'DERIBIT'``)."""
    if isinstance(exchange_code, ExchangeCode):
        code = exchange_code
    else:
        try:
            code = ExchangeCode(exchange_code)
        except ValueError:
            code = ExchangeCode[exchange_code]
    return _EXCHANGES[code]
