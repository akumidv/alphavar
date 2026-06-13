"""Canned Deribit API responses for hermetic tests (T11).

Records mirror the inline data already used by the ``test__normalize_book_*`` tests, so a
mocked ``get_book_summary_by_currency`` returns the same shapes those tests assert on (no
live API). The mock transport wraps each list as ``{"jsonrpc": "2.0", "result": [...]}``.
"""

# /public/get_instruments — covers future / option / spot kinds.
GET_INSTRUMENTS = [
    {"price_index": "btc_usd", "instrument_name": "BTC-31JAN25", "kind": "future",
     "is_active": True, "expiration_timestamp": 1738310400000, "strike": None, "option_type": None},
    {"price_index": "btc_usd", "instrument_name": "BTC-31JAN25-92000-P", "kind": "option",
     "is_active": True, "expiration_timestamp": 1738310400000, "strike": 92000.0, "option_type": "put"},
    {"price_index": "btc_usdc", "instrument_name": "BTC_USDC", "kind": "spot",
     "is_active": True, "expiration_timestamp": 32503708800000, "strike": None, "option_type": None},
]

# kind=future — from test__normalize_book_future inline data.
BOOK_FUTURE = [
    {"high": 104960.0, "low": 92342.5, "last": 101019.0, "instrument_name": "BTC-27JUN25",
     "bid_price": 90505.0, "ask_price": 111500.0, "open_interest": 390279240, "mark_price": 96760.58,
     "price_change": 0.5765, "volume": 216.69274001, "base_currency": "BTC",
     "creation_timestamp": 1736993696792, "estimated_delivery_price": 100064.33, "quote_currency": "USD",
     "volume_usd": 21776140.0, "volume_notional": 21776140.0, "mid_price": 101002.5,
     "current_funding": None, "funding_8h": None},
    {"high": 99776.0, "low": 91995.0, "last": 99677.5, "instrument_name": "BTC-31JAN25",
     "bid_price": None, "ask_price": None, "open_interest": 46864950, "mark_price": 99400.67,
     "price_change": 3.7362, "volume": 129.95052186, "base_currency": "BTC",
     "creation_timestamp": 1736993696792, "estimated_delivery_price": 100064.33, "quote_currency": "USD",
     "volume_usd": 12489490.0, "volume_notional": 12489490.0, "mid_price": None,
     "current_funding": None, "funding_8h": None},
    {"high": 102500.0, "low": 93739.26, "last": 97678.0, "instrument_name": "BTC-28FEB25",
     "bid_price": 89782.5, "ask_price": 102500.0, "open_interest": 21660580, "mark_price": 97707.42,
     "price_change": 4.2018, "volume": 206.28117084, "base_currency": "BTC",
     "creation_timestamp": 1736993696792, "estimated_delivery_price": 100064.33, "quote_currency": "USD",
     "volume_usd": 20245610.0, "volume_notional": 20245610.0, "mid_price": 96141.25,
     "current_funding": None, "funding_8h": None},
]

# kind=option — from test__normalize_book_option inline data (BTC rows only, to keep the
# single-currency mock consistent; the parser handles mixed currencies elsewhere).
BOOK_OPTION = [
    {"high": None, "low": None, "last": None, "bid_price": 0.101, "ask_price": 0.2385,
     "instrument_name": "BTC-7FEB25-106000-P", "open_interest": 0.0, "mark_price": 0.1042716,
     "price_change": None, "interest_rate": 0.0, "volume": 0.0, "mark_iv": 60.86,
     "underlying_price": 98763.21, "underlying_index": "SYN.BTC-7FEB25", "base_currency": "BTC",
     "creation_timestamp": 1737074222663, "estimated_delivery_price": 100143.63,
     "quote_currency": "BTC", "volume_usd": 0.0, "mid_price": 0.16975},
    {"high": 0.0145, "low": 0.0145, "last": 0.0145, "bid_price": 0.018, "ask_price": 0.019,
     "instrument_name": "BTC-31JAN25-92000-P", "open_interest": 135.94, "mark_price": 0.01866323,
     "price_change": None, "interest_rate": 0.0, "volume": 3.21, "mark_iv": 60.13,
     "underlying_price": 99067.37, "underlying_index": "BTC-31JAN25", "base_currency": "BTC",
     "creation_timestamp": 1737074222663, "estimated_delivery_price": 100143.63,
     "quote_currency": "BTC", "volume_usd": 4624.81, "mid_price": 0.0185},
    {"high": None, "low": None, "last": None, "bid_price": None, "ask_price": None,
     "instrument_name": "BTC-27JUN25-230000-C", "open_interest": 0.0, "mark_price": 0.01184211,
     "price_change": None, "interest_rate": 0.0, "volume": 0.0, "mark_iv": 74.14,
     "underlying_price": 96813.04, "underlying_index": "BTC-27JUN25", "base_currency": "BTC",
     "creation_timestamp": 1737074222663, "estimated_delivery_price": 100143.63,
     "quote_currency": "BTC", "volume_usd": 0.0, "mid_price": None},
]

# kind=spot — from test__normalize_book_spot inline data (BTC base rows).
BOOK_SPOT = [
    {"high": 96825.2923, "low": 81192.0, "last": 81192.0, "instrument_name": "BTC_USDC",
     "bid_price": 63933.0, "ask_price": 81192.0, "mark_price": 100031.0749, "price_change": 0.0,
     "volume": 10.5283, "base_currency": "BTC", "creation_timestamp": 1736991799679,
     "estimated_delivery_price": 100031.0749, "quote_currency": "USDC", "volume_usd": 1011551.12,
     "volume_notional": 1011146.6566, "mid_price": 72562.5},
    {"high": 56363.5, "low": 56363.5, "last": 56363.5, "instrument_name": "BTC_EURR",
     "bid_price": 141.87, "ask_price": 56363.5, "mark_price": 97099.1846, "price_change": 0.0,
     "volume": 0.0005, "base_currency": "BTC", "creation_timestamp": 1736991799679,
     "estimated_delivery_price": 97099.1846, "quote_currency": "EURR", "volume_usd": 29.02,
     "volume_notional": 28.18175, "mid_price": 28252.685},
]

# kind=future_combo — from test__normalize_book_future_combo inline data.
BOOK_FUTURE_COMBO = [
    {"high": None, "low": None, "last": None, "instrument_name": "BTC-FS-26SEP25_24JAN25",
     "bid_price": None, "ask_price": None, "mark_price": 2265.11, "price_change": None, "volume": 0.0,
     "base_currency": "BTC", "creation_timestamp": 1737073906519, "estimated_delivery_price": 100173.8,
     "quote_currency": "USD", "volume_usd": 0.0, "volume_notional": 0.0, "mid_price": None},
    {"high": None, "low": None, "last": None, "instrument_name": "BTC-FS-28FEB25_31JAN25",
     "bid_price": None, "ask_price": None, "mark_price": -1258.25, "price_change": None, "volume": 0.0,
     "base_currency": "BTC", "creation_timestamp": 1737073906519, "estimated_delivery_price": 100173.8,
     "quote_currency": "USD", "volume_usd": 0.0, "volume_notional": 0.0, "mid_price": None},
]

# kind=option_combo — strategy combos (no per-leg strike/type at top level).
BOOK_OPTION_COMBO = [
    {"high": None, "low": None, "last": 0.001, "instrument_name": "BTC-CBUT-31JAN25-90000_95000_100000",
     "bid_price": None, "ask_price": None, "open_interest": 0.0, "mark_price": 0.001,
     "price_change": None, "interest_rate": 0.0, "volume": 0.0, "mark_iv": 0.0,
     "underlying_price": 99067.37, "underlying_index": "BTC-31JAN25", "base_currency": "BTC",
     "creation_timestamp": 1737074222663, "estimated_delivery_price": 100143.63,
     "quote_currency": "BTC", "volume_usd": 0.0, "mid_price": None},
]
