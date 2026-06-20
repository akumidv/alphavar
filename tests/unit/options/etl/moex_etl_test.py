import datetime

import pandas as pd
import pytest

from alphavar.options.dictionary import OptionsTerm, Timeframe
from alphavar.options.etl.etl_class import AssetBookData
from alphavar.options.etl.moex_etl import EtlMoex


class TestEtlMoex(EtlMoex):
    def _save_tasks_dataframes_job(self):
        """Stop saving test tasks during tests"""


@pytest.fixture(name="etl_moex")
def etl_moex_fixture(moex_exchange, data_path):
    """Fixture for Moex ETL"""
    etl_moex = TestEtlMoex(moex_exchange, None, Timeframe.EOD, data_path)
    return etl_moex


@pytest.mark.integration  # fetches a live book snapshot from the MOEX API
def test_moex_get_symbols_books_snapshot(etl_moex, moex_asset_code):
    request_timestamp = pd.Timestamp.now(tz=datetime.UTC)
    book_data = etl_moex.get_symbols_books_snapshot(moex_asset_code, request_timestamp)
    assert isinstance(book_data, AssetBookData)
    assert book_data.asset_name == moex_asset_code
    assert book_data.request_timestamp == request_timestamp
    assert isinstance(book_data.options, pd.DataFrame)


def test__save_timeframe_book_update(etl_moex):
    options_df = pd.DataFrame(
        {f"{OptionsTerm.ASSET_CODE}": ["SI", "SI", "YDEX", "YDEX"], f"{OptionsTerm.PRICE}": [10, 10, 50, 50]}
    )
    future_df = pd.DataFrame({f"{OptionsTerm.ASSET_CODE}": ["SI", "SI"], f"{OptionsTerm.PRICE}": [80, 80]})
    # 4VERIFY (owner): a spot row is identified by asset_code (not base_code) —
    # spot has no underlying; matches _save_timeframe_book_update's groupby (SPOT -> asset_code)
    # and MOEX normalization (secid -> asset_code). Was base_code, which raised KeyError.
    spot_df = pd.DataFrame({f"{OptionsTerm.ASSET_CODE}": ["YDEX", "YDEX"], f"{OptionsTerm.PRICE}": [4000, 4000]})
    saved_tasks = len(etl_moex._save_tasks)
    book_data = AssetBookData(
        asset_name="BTC",
        request_timestamp=pd.Timestamp.now(tz=datetime.UTC),
        options=options_df,
        futures=future_df,
        spot=spot_df,
    )
    etl_moex._save_timeframe_book_update(book_data)  # pylint: disable=protected-access
    assert len(etl_moex._save_tasks) == saved_tasks + len(options_df[OptionsTerm.ASSET_CODE].unique()) + len(
        future_df[OptionsTerm.ASSET_CODE].unique()
    ) + len(spot_df[OptionsTerm.ASSET_CODE].unique())
    etl_moex._save_tasks = []
