"""Deribit fixture recording — declares which Deribit calls to capture.

Reuses the real `alphavar.exchange.deribit` API (no re-implemented requests). Currency
`BTC` matches the test fixtures. Note: Deribit rejects ``kind=options`` (the venue wants
singular ``option``) — see the backlog item on splitting project enums from API enums;
the bad call is skipped best-effort.
"""
from alphavar.exchange._abstract_exchange import RequestClass
from alphavar.exchange.deribit import DeribitExchange, DeribitMarket, DeribitAssetKind

from agents._dev.tools.exchange_fixtures._record import record, try_call

CURRENCY = 'BTC'


def _drive(make_spy):
    client = make_spy(RequestClass(api_url=DeribitExchange.PRODUCT_API_URL))
    market = DeribitMarket(client)
    try_call('get_instruments', market.get_instruments)
    for kind in (DeribitAssetKind.FUTURE, DeribitAssetKind.OPTION, DeribitAssetKind.SPOT,
                 DeribitAssetKind.FUTURE_COMBO, DeribitAssetKind.OPTION_COMBO):
        try_call(f'book {kind.value}',
                 lambda k=kind: market.get_book_summary_by_currency(currency=CURRENCY, kind=k))
    try_call('book no-kind', lambda: market.get_book_summary_by_currency(currency=CURRENCY))


def run():
    record('deribit', _drive)
