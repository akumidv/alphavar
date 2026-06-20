import datetime

import pandas as pd
import pytest

from alphavar.io.exchange import DeribitExchange
from alphavar.options.dictionary import OptionsTerm, Timeframe
from alphavar.options.etl.deribit_etl import DeribitAssetBookData, EtlDeribit


class TestEtlDeribit(EtlDeribit):
    def _save_tasks_dataframes_job(self):
        """Stop saving test tasks during tests"""


@pytest.fixture(name="etl_deribit")
def etl_deribit_fixture(deribit_client, data_path):
    """Fixture for Deribit ETL"""
    etl_deribit = TestEtlDeribit(deribit_client, None, Timeframe.EOD, data_path)
    return etl_deribit


@pytest.mark.integration  # fetches a live book snapshot from the Deribit API
def test_get_symbols_books_snapshot(etl_deribit):
    currency_symbol = DeribitExchange.CURRENCIES[0]
    request_timestamp = pd.Timestamp.now(tz=datetime.UTC)
    book_data = etl_deribit.get_symbols_books_snapshot(currency_symbol, request_timestamp)
    assert isinstance(book_data, DeribitAssetBookData)
    assert book_data.asset_name == currency_symbol
    assert book_data.request_timestamp == request_timestamp
    assert isinstance(book_data.options, pd.DataFrame)
    assert isinstance(book_data.futures, pd.DataFrame)
    assert isinstance(book_data.spot, pd.DataFrame)
    assert isinstance(book_data.future_combo, pd.DataFrame)
    assert isinstance(book_data.option_combo, pd.DataFrame)


def test__save_timeframe_book_update(etl_deribit):
    options_df = pd.DataFrame(
        {
            f"{OptionsTerm.ASSET_CODE}": ["BTC-USD", "BTC-USD", "ETH-USD", "ETH-USD"],
            f"{OptionsTerm.PRICE}": [100, 100, 50, 50],
        }
    )
    future_df = pd.DataFrame(
        {f"{OptionsTerm.ASSET_CODE}": ["BTC", "BTC", "ETH", "ETH"], f"{OptionsTerm.PRICE}": [100, 100, 50, 50]}
    )
    spot_df = pd.DataFrame(
        {f"{OptionsTerm.ASSET_CODE}": ["BTC", "BTC", "ETH", "ETH"], f"{OptionsTerm.PRICE}": [100, 100, 50, 50]}
    )
    futures_combo_df = pd.DataFrame(
        {f"{OptionsTerm.ASSET_CODE}": ["BTC", "BTC", "ETH", "ETH"], f"{OptionsTerm.PRICE}": [100, 100, 50, 50]}
    )
    option_combo_df = pd.DataFrame(
        {f"{OptionsTerm.ASSET_CODE}": ["BTC", "BTC", "ETH", "ETH"], f"{OptionsTerm.PRICE}": [100, 100, 50, 50]}
    )
    saved_tasks = len(etl_deribit._save_tasks)
    book_data = DeribitAssetBookData(
        asset_name="BTC",
        request_timestamp=pd.Timestamp.now(tz=datetime.UTC),
        options=options_df,
        futures=future_df,
        spot=spot_df,
        future_combo=futures_combo_df,
        option_combo=option_combo_df,
    )
    etl_deribit._save_timeframe_book_update(book_data)  # pylint: disable=protected-access
    assert len(etl_deribit._save_tasks) == 10 + saved_tasks
    etl_deribit._save_tasks = []
