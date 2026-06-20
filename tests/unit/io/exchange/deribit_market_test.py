"""Deribit exchange provider"""

import datetime

import pandas as pd

from alphavar.io.exchange import RequestClass
from alphavar.io.exchange.deribit import DeribitAssetKind, DeribitExchange, DeribitMarket
from alphavar.options.dictionary import (
    OptionsTerm,
)

# The `deribit_market` fixture is provided by conftest.py with a mocked HTTP transport
# (hermetic — no live API, T11).


def test_deribit_market_init():
    client = RequestClass(api_url=DeribitExchange.TEST_API_URL)
    deribit_market = DeribitMarket(client)
    assert isinstance(deribit_market, DeribitMarket)


def test_get_instruments(deribit_market):
    symbols_df = deribit_market.get_instruments()
    assert isinstance(symbols_df, pd.DataFrame)
    assert len(symbols_df) > 0
    assert "price_index" in symbols_df.columns
    assert not symbols_df[symbols_df["price_index"] == "btc_usd"].empty


def test_get_book_summary_by_currency(deribit_market):
    book_summary_df = deribit_market.get_book_summary_by_currency(currency=DeribitExchange.CURRENCIES[0])
    assert isinstance(book_summary_df, pd.DataFrame)
    assert len(book_summary_df) > 0
    assert "base_currency" in book_summary_df.columns
    assert not book_summary_df[book_summary_df["base_currency"] == DeribitExchange.CURRENCIES[0]].empty


def test__normalize_book_spot(deribit_market):
    spot_df = pd.DataFrame(
        {
            "high": [0.0349, 96825.2923, 56363.5, 105141.8784, None],
            "low": [0.0348, 81192.0, 56363.5, 105141.8784, None],
            "last": [0.0348, 81192.0, 56363.5, 105141.8784, 22.3286],
            "instrument_name": ["ETH_BTC", "BTC_USDC", "BTC_EURR", "BTC_USYC", "BTC_PAXG"],
            "bid_price": [0.0356, 63933.0, 141.87, None, None],
            "ask_price": [0.0461, 81192.0, 56363.5, None, 22.0304],
            "mark_price": [0.033988, 100031.0749, 97099.1846, 93125.797049, 37.0976],
            "price_change": [-0.2865, 0.0, 0.0, 0.0, None],
            "volume": [0.3046, 10.5283, 0.0005, 0.0001, 0.0],
            "base_currency": ["ETH", "BTC", "BTC", "BTC", "BTC"],
            "creation_timestamp": [1736991799679, 1736991799679, 1736991799679, 1736991799679, 1736991799679],
            "estimated_delivery_price": [0.033988, 100031.0749, 97099.1846, 93125.797049, 37.0976],
            "quote_currency": ["BTC", "USDC", "EURR", "USYC", "PAXG"],
            "volume_usd": [1044.26, 1011551.12, 29.02, 11.3, 0.0],
            "volume_notional": [0.01061433, 1011146.6566, 28.18175, 10.514188, 0.0],
            "mid_price": [0.04085, 72562.5, 28252.685, None, None],
        }
    )
    df = deribit_market._normalize_book(spot_df, pd.Timestamp.now(tz=datetime.UTC))
    assert OptionsTerm.ASSET_CODE in df.columns
    assert OptionsTerm.INSTRUMENT_KIND in df.columns
    assert list(df[OptionsTerm.INSTRUMENT_KIND].unique()) == [DeribitAssetKind.SPOT.code]


def test_get_book_summary_by_currency_option_spot(deribit_market):
    book_summary_df = deribit_market.get_book_summary_by_currency(
        currency=DeribitExchange.CURRENCIES[0], kind=DeribitAssetKind.SPOT
    )
    assert isinstance(book_summary_df, pd.DataFrame)
    assert len(book_summary_df) > 0
    assert "base_currency" in book_summary_df.columns
    assert not book_summary_df[book_summary_df["base_currency"] == DeribitExchange.CURRENCIES[0]].empty


def test__normalize_book_future(deribit_market):
    fut_df = pd.DataFrame(
        {
            "high": [104960.0, 99776.0, 102500.0, 104836.0, 97900.0],
            "low": [92342.5, 91995.0, 93739.26, 102017.18, 91562.5],
            "last": [101019.0, 99677.5, 97678.0, 104750.0, 97457.0],
            "instrument_name": ["BTC-27JUN25", "BTC-31JAN25", "BTC-28FEB25", "BTC-26SEP25", "BTC-28MAR25"],
            "bid_price": [90505.0, None, 89782.5, 90505.0, 95900.0],
            "ask_price": [111500.0, None, 102500.0, 119000.0, 105590.0],
            "open_interest": [390279240, 46864950, 21660580, 239016160, 472960750],
            "mark_price": [96760.58, 99400.67, 97707.42, 104378.95, 97477.14],
            "price_change": [0.5765, 3.7362, 4.2018, 1.0234, 3.2583],
            "volume": [216.69274001, 129.95052186, 206.28117084, 71.6209281, 374.26395344],
            "base_currency": ["BTC", "BTC", "BTC", "BTC", "BTC"],
            "creation_timestamp": [1736993696792, 1736993696792, 1736993696792, 1736993696792, 1736993696792],
            "estimated_delivery_price": [100064.33, 100064.33, 100064.33, 100064.33, 100064.33],
            "quote_currency": ["USD", "USD", "USD", "USD", "USD"],
            "volume_usd": [21776140.0, 12489490.0, 20245610.0, 7494340.0, 36170390.0],
            "volume_notional": [21776140.0, 12489490.0, 20245610.0, 7494340.0, 36170390.0],
            "mid_price": [101002.5, None, 96141.25, 104752.5, 100745.0],
            "current_funding": [None, None, None, None, None],
            "funding_8h": [None, None, None, None, None],
        }
    )
    df = deribit_market._normalize_book(fut_df, pd.Timestamp.now(tz=datetime.UTC))
    assert OptionsTerm.ASSET_CODE in df.columns
    assert OptionsTerm.EXCH_SYMBOL in df.columns
    assert OptionsTerm.INSTRUMENT_KIND in df.columns
    assert list(df[OptionsTerm.INSTRUMENT_KIND].unique()) == [DeribitAssetKind.FUTURE.code]
    assert None not in list(df[OptionsTerm.EXPIRATION_DATE].unique())
    assert df[OptionsTerm.PRICE].notnull().any()


def test_get_book_summary_by_currency_future(deribit_market):
    book_summary_df = deribit_market.get_book_summary_by_currency(
        currency=DeribitExchange.CURRENCIES[0], kind=DeribitAssetKind.FUTURE
    )
    assert isinstance(book_summary_df, pd.DataFrame)
    assert len(book_summary_df) > 0
    assert "base_currency" in book_summary_df.columns
    assert not book_summary_df[book_summary_df["base_currency"] == DeribitExchange.CURRENCIES[0]].empty
    assert list(book_summary_df[OptionsTerm.INSTRUMENT_KIND].unique()) == [DeribitAssetKind.FUTURE.code]
    assert book_summary_df[OptionsTerm.PRICE].notnull().any()


def test__normalize_book_future_combo(deribit_market):
    fut_combo_df = pd.DataFrame(
        {
            "high": [None, None, None, None, None],
            "low": [None, None, None, None, None],
            "last": [None, None, None, None, None],
            "instrument_name": [
                "BTC-FS-26SEP25_24JAN25",
                "BTC-FS-28FEB25_24JAN25",
                "BTC-FS-28FEB25_31JAN25",
                "BTC-FS-26DEC25_17JAN25",
                "BTC-FS-28MAR25_17JAN25",
            ],
            "bid_price": [None, None, None, None, None],
            "ask_price": [None, None, None, None, None],
            "mark_price": [2265.11, -4364.62, -1258.25, -792.67, -1001.75],
            "price_change": [None, None, None, None, None],
            "volume": [0.0, 0.0, 0.0, 0.0, 0.0],
            "base_currency": ["BTC", "BTC", "BTC", "BTC", "BTC"],
            "creation_timestamp": [1737073906519, 1737073906519, 1737073906519, 1737073906519, 1737073906519],
            "estimated_delivery_price": [100173.8, 100173.8, 100173.8, 100173.8, 100173.8],
            "quote_currency": ["USD", "USD", "USD", "USD", "USD"],
            "volume_usd": [0.0, 0.0, 0.0, 0.0, 0.0],
            "volume_notional": [0.0, 0.0, 0.0, 0.0, 0.0],
            "mid_price": [None, None, None, None, None],
        }
    )
    df = deribit_market._normalize_book(fut_combo_df, pd.Timestamp.now(tz=datetime.UTC))
    assert OptionsTerm.ASSET_CODE in df.columns
    assert OptionsTerm.EXCH_SYMBOL in df.columns
    assert OptionsTerm.INSTRUMENT_KIND in df.columns
    assert list(df[OptionsTerm.INSTRUMENT_KIND].unique()) == [DeribitAssetKind.FUTURE_COMBO.code]
    assert None not in list(df[OptionsTerm.EXPIRATION_DATE].unique())


def test_get_book_summary_by_currency_future_combo(deribit_market):
    book_summary_df = deribit_market.get_book_summary_by_currency(
        currency=DeribitExchange.CURRENCIES[0], kind=DeribitAssetKind.FUTURE_COMBO
    )

    assert isinstance(book_summary_df, pd.DataFrame)
    assert len(book_summary_df) > 0
    assert "base_currency" in book_summary_df.columns
    assert not book_summary_df[book_summary_df["base_currency"] == DeribitExchange.CURRENCIES[0]].empty
    assert list(book_summary_df[OptionsTerm.INSTRUMENT_KIND].unique()) == [DeribitAssetKind.FUTURE_COMBO.code]
    assert None not in list(book_summary_df[OptionsTerm.EXPIRATION_DATE].unique())
    assert book_summary_df[OptionsTerm.PRICE].notnull().any()


def test__normalize_book_option(deribit_market):
    opt_df = pd.DataFrame(
        {
            "high": [None, None, None, None, 0.0145, None, None],
            "low": [None, None, None, None, 0.0145, None, None],
            "last": [None, None, 0.0001, None, 0.0145, None, None],
            "bid_price": [0.101, None, None, None, 0.018, 0.1070, None],
            "ask_price": [0.2385, None, None, None, 0.019, 0.1460, None],
            "instrument_name": [
                "BTC-7FEB25-106000-P",
                "BTC-18JAN25-107000-P",
                "BTC-24JAN25-60000-P",
                "BTC-27JUN25-230000-C",
                "BTC-31JAN25-92000-P",
                "ETH-18JAN25-3000-C",
                "DOGE_USDC-7FEB25-0d4064-C",
            ],
            "open_interest": [0.0, 0.0, 0.0, 0.0, 135.94, 0.0, 0.0],
            "mark_price": [0.1042716, 0.05807133, 0.0, 0.01184211, 0.01866323, 0.107292, 0.001296],
            "price_change": [None, None, None, None, None, None, None],
            "interest_rate": [0.0, 0.0, 0.0, 0.0, 0.0, None, None],
            "volume": [0.0, 0.0, 0.0, 0.0, 3.21, 0.0, 0.0],
            "mark_iv": [60.86, 41.39, 0.0, 74.14, 60.13, 0.0, 0.0],
            "underlying_price": [98763.21, 101136.99285714286, 102188.24, 96813.04, 99067.37, 3359.61, 0.385358],
            "underlying_index": [
                "SYN.BTC-7FEB25",
                "SYN.BTC-18JAN25",
                "BTC-24JAN25",
                "BTC-27JUN25",
                "BTC-31JAN25",
                "index_price",
                "SYN.DOGE_USDC-7FEB25",
            ],
            "base_currency": ["BTC", "BTC", "BTC", "BTC", "BTC", "ETH", "DOGE"],
            "creation_timestamp": [
                1737074222663,
                1737074222663,
                1737074222663,
                1737074222663,
                1737074222663,
                1737088726575,
                1737088730082,
            ],
            "estimated_delivery_price": [100143.63, 100143.63, 100143.63, 100143.63, 100143.63, 3359.61, 0.385417],
            "quote_currency": ["BTC", "BTC", "BTC", "BTC", "BTC", "ETH", "USDC"],
            "volume_usd": [0.0, 0.0, 0.0, 0.0, 4624.81, 0.0, 0.0],
            "mid_price": [0.16975, None, None, None, 0.0185, 0.12650, None],
        }
    )
    df = deribit_market._normalize_book(opt_df, pd.Timestamp.now(tz=datetime.UTC))
    assert OptionsTerm.ASSET_CODE in df.columns
    assert OptionsTerm.EXCH_SYMBOL in df.columns
    assert OptionsTerm.INSTRUMENT_KIND in df.columns
    assert list(df[OptionsTerm.INSTRUMENT_KIND].unique()) == [DeribitAssetKind.OPTION.code]
    assert None not in list(df[OptionsTerm.EXPIRATION_DATE].unique())
    assert None not in list(df[OptionsTerm.STRIKE].unique())
    assert None not in list(df[OptionsTerm.OPTION_RIGHT].unique())
    assert df[OptionsTerm.PRICE].notnull().any()


def test_get_book_summary_by_currency_option(deribit_market):
    book_summary_df = deribit_market.get_book_summary_by_currency(
        currency=DeribitExchange.CURRENCIES[0], kind=DeribitAssetKind.OPTION
    )
    assert isinstance(book_summary_df, pd.DataFrame)
    assert len(book_summary_df) > 0
    assert "base_currency" in book_summary_df.columns
    assert not book_summary_df[book_summary_df["base_currency"] == DeribitExchange.CURRENCIES[0]].empty
    assert None not in list(book_summary_df[OptionsTerm.EXPIRATION_DATE].unique())
    assert None not in list(book_summary_df[OptionsTerm.STRIKE].unique())
    assert None not in list(book_summary_df[OptionsTerm.OPTION_RIGHT].unique())
    assert book_summary_df[OptionsTerm.PRICE].notnull().any()


def test__normalize_book_option_combo(deribit_market):
    opt_combo_df = pd.DataFrame(
        {
            "high": [None, None, None, None, None],
            "low": [None, None, None, None, None],
            "last": [None, None, None, None, None],
            "instrument_name": [
                "BTC-CSR13-17JAN25-50000_55000",
                "BTC-CSR13-31JAN25-100000_110000",
                "BTC-CSR13-31JAN25-44000_110000",
                "BTC-PSR13-31JAN25-96000_94000",
                "BTC-CBUT-28MAR25-90000_95000_100000",
            ],
            "bid_price": [None, 0.0001, None, None, 0.0001],
            "ask_price": [None, 0.005, None, None, None],
            "mark_price": [-0.86082998, -0.02057613, 0.49287308, -0.04157543, 0.00473082],
            "price_change": [None, None, None, None, None],
            "volume": [0.0, 0.0, 0.0, 0.0, 0.0],
            "base_currency": ["BTC", "BTC", "BTC", "BTC", "BTC"],
            "creation_timestamp": [1737074402953, 1737074402953, 1737074402953, 1737074402953, 1737074402953],
            "estimated_delivery_price": [100216.53, 100216.53, 100216.53, 100216.53, 100216.53],
            "quote_currency": ["BTC", "BTC", "BTC", "BTC", "BTC"],
            "volume_usd": [0.0, 0.0, 0.0, 0.0, 0.0],
            "mid_price": [None, 0.00255, None, None, None],
        }
    )
    df = deribit_market._normalize_book(opt_combo_df, pd.Timestamp.now(tz=datetime.UTC))
    assert OptionsTerm.ASSET_CODE in df.columns
    assert OptionsTerm.EXCH_SYMBOL in df.columns
    assert OptionsTerm.INSTRUMENT_KIND in df.columns
    assert list(df[OptionsTerm.INSTRUMENT_KIND].unique()) == [DeribitAssetKind.OPTION_COMBO.code]


def test_get_book_summary_by_currency_option_combo(deribit_market):
    book_summary_df = deribit_market.get_book_summary_by_currency(
        currency=DeribitExchange.CURRENCIES[0], kind=DeribitAssetKind.OPTION_COMBO
    )
    assert isinstance(book_summary_df, pd.DataFrame)
    assert len(book_summary_df) > 0
    assert "base_currency" in book_summary_df.columns
    assert not book_summary_df[book_summary_df["base_currency"] == DeribitExchange.CURRENCIES[0]].empty
