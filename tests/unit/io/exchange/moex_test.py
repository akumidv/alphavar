"""MOEX exchange provider"""

import pandas as pd
import pytest

from alphavar.core.dictionary import InstrumentKind
from alphavar.io.exchange import AbstractExchange
from alphavar.io.exchange.moex import MoexExchange
from alphavar.io.provider import AbstractProvider
from alphavar.options.dictionary import OptionsTerm


def test_moex_exchange_init():
    moex = MoexExchange()
    assert isinstance(moex, AbstractExchange)
    assert isinstance(moex, AbstractProvider)


def test_get_assets_list_future(moex_exchange, moex_asset_code):
    asset_kind = InstrumentKind.FUTURE
    assets = moex_exchange.get_assets_list(asset_kind)
    assert isinstance(assets, list)
    assert len(assets) > 0
    assert moex_asset_code in assets


@pytest.mark.integration  # walks every asset's /options endpoint (live API)
def test_get_assets_list_options(moex_exchange, moex_asset_code):
    asset_kind = InstrumentKind.OPTION
    assets = moex_exchange.get_assets_list(asset_kind)
    assert isinstance(assets, list)
    assert len(assets) > 0
    assert moex_asset_code in assets


def test_get_options_assets_books_snapshot(moex_exchange, moex_asset_code):
    # Single-asset (SI) book-summary join — hermetic now that its series/underlyings/desk
    # calls are recorded (fixtures). The whole-market default (asset_codes=None) is still a
    # live-API walk and stays out of the suite.
    book_summary_df = moex_exchange.get_options_assets_books_snapshot(moex_asset_code)
    assert isinstance(book_summary_df, pd.DataFrame)
    assert len(book_summary_df) > 0
    # R4.1.1 split: asset_code = underlying, exch_symbol = venue contract.
    assert OptionsTerm.ASSET_CODE in book_summary_df.columns
    assert OptionsTerm.EXCH_SYMBOL in book_summary_df.columns
    assert not book_summary_df[book_summary_df[OptionsTerm.ASSET_CODE] == moex_asset_code].empty
    # the underlying-future merge matched (exch_symbol -> underlying_code), so it populated.
    assert book_summary_df[OptionsTerm.UNDERLYING_EXPIRATION_DATE].notna().any()
