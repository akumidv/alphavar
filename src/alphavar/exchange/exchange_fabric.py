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
