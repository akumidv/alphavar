"""Deribit exchange provider"""

from functools import lru_cache

import pandas as pd
import pytest
from pydantic import ValidationError

from alphavar.io.exchange import RequestClass
from alphavar.io.exchange.moex import MoexAssetType, MoexExchange, MoexOptions
from alphavar.options.dictionary import (
    OptionsTerm,
)


@pytest.fixture(name="moex_option_series_code")
@lru_cache
def moex_option_series_code_fixture(moex_options_client, moex_asset_code):
    opt_df = moex_options_client.get_option_series(asset_code=moex_asset_code)
    series_code = opt_df.iloc[0][OptionsTerm.SERIES_CODE]
    return series_code


def test_moex_market_init():
    client = RequestClass(api_url=MoexExchange.TEST_API_URL)
    deribit_market = MoexOptions(client)
    assert isinstance(deribit_market, MoexOptions)


def test_get_assets(moex_options_client, moex_asset_code):
    symbols_df = moex_options_client.get_assets()
    assert isinstance(symbols_df, pd.DataFrame)
    assert len(symbols_df) > 0
    assert OptionsTerm.ASSET_CODE in symbols_df.columns
    assert OptionsTerm.INSTRUMENT_KIND in symbols_df.columns
    assert not symbols_df[symbols_df[OptionsTerm.INSTRUMENT_KIND] == MoexAssetType.SHARE.code].empty
    assert not symbols_df[symbols_df[OptionsTerm.ASSET_CODE] == moex_asset_code].empty


def test_get_asset_info(moex_options_client, moex_asset_code):
    asset_data = moex_options_client.get_asset_info(asset_code=moex_asset_code, asset_type=MoexAssetType.FUTURES)
    assert isinstance(asset_data, pd.Series)
    assert OptionsTerm.ASSET_CODE in asset_data
    assert OptionsTerm.INSTRUMENT_KIND in asset_data
    assert asset_data[OptionsTerm.ASSET_CODE] == moex_asset_code


def test_get_asset_info_for_wrong_parameters_should_raise_error(moex_options_client, moex_asset_code):
    with pytest.raises(ValidationError):
        _ = moex_options_client.get_asset_info(asset_code=None)
    with pytest.raises(ValueError):
        _ = moex_options_client.get_asset_info(asset_code=moex_asset_code, asset_type="123")


def test_get_asset_futures(moex_options_client, moex_asset_code):
    asset_futures_df = moex_options_client.get_asset_futures(asset_code=moex_asset_code)
    assert isinstance(asset_futures_df, pd.DataFrame)
    assert len(asset_futures_df) > 0
    assert OptionsTerm.ASSET_CODE in asset_futures_df.columns
    assert OptionsTerm.INSTRUMENT_KIND in asset_futures_df.columns
    assert OptionsTerm.ASSET_CODE in asset_futures_df.columns
    assert OptionsTerm.EXPIRATION_DATE in asset_futures_df.columns
    assert not asset_futures_df[asset_futures_df[OptionsTerm.INSTRUMENT_KIND] == MoexAssetType.FUTURES.code].empty
    assert not asset_futures_df[asset_futures_df[OptionsTerm.ASSET_CODE] == moex_asset_code].empty


def test_get_asset_options(moex_options_client, moex_asset_code):
    opt_df = moex_options_client.get_asset_options(asset_code=moex_asset_code)
    assert isinstance(opt_df, pd.DataFrame)
    assert len(opt_df) > 0
    assert OptionsTerm.ASSET_CODE in opt_df.columns
    assert OptionsTerm.UNDERLYING_CODE in opt_df.columns
    assert OptionsTerm.UNDERLYING_ASSET_CLASS in opt_df.columns
    assert OptionsTerm.ASSET_CODE in opt_df.columns
    assert OptionsTerm.EXPIRATION_DATE in opt_df.columns
    assert not opt_df[opt_df[OptionsTerm.UNDERLYING_ASSET_CLASS] == MoexAssetType.FUTURES.code].empty
    assert not opt_df[opt_df[OptionsTerm.ASSET_CODE] == moex_asset_code].empty


def test_get_asset_options_for_asset_wo_option(moex_options_client):
    asset_options_df = moex_options_client.get_asset_options(asset_code="AFLT")
    assert asset_options_df is None


def test_get_asset_option_series(moex_options_client, moex_asset_code):
    opt_df = moex_options_client.get_option_series(asset_code=moex_asset_code)
    print(opt_df)
    assert isinstance(opt_df, pd.DataFrame)
    assert len(opt_df) > 0
    assert OptionsTerm.UNDERLYING_CODE in opt_df.columns
    assert OptionsTerm.UNDERLYING_ASSET_CLASS in opt_df.columns
    assert OptionsTerm.ASSET_CODE in opt_df.columns
    assert OptionsTerm.EXPIRATION_DATE in opt_df.columns
    assert OptionsTerm.OPEN_INTEREST in opt_df.columns
    assert OptionsTerm.VOLUME in opt_df.columns
    assert not opt_df[opt_df[OptionsTerm.UNDERLYING_ASSET_CLASS] == MoexAssetType.FUTURES.code].empty
    assert not opt_df[opt_df[OptionsTerm.ASSET_CODE] == moex_asset_code].empty


def test_get_asset_option_series_list(moex_options_client, moex_asset_code, moex_option_series_code):
    opt_df = moex_options_client.get_option_series_list(asset_code=moex_asset_code, series_code=moex_option_series_code)
    assert isinstance(opt_df, pd.DataFrame)
    assert len(opt_df) > 0
    assert OptionsTerm.ASSET_CODE in opt_df.columns
    assert OptionsTerm.UNDERLYING_CODE in opt_df.columns
    assert OptionsTerm.UNDERLYING_ASSET_CLASS in opt_df.columns
    assert OptionsTerm.ASSET_CODE in opt_df.columns
    assert OptionsTerm.EXPIRATION_DATE in opt_df.columns
    assert not opt_df[opt_df[OptionsTerm.UNDERLYING_ASSET_CLASS] == MoexAssetType.FUTURES.code].empty
    assert not opt_df[opt_df[OptionsTerm.ASSET_CODE] == moex_asset_code].empty


def test_get_option_series_desk(moex_options_client, moex_asset_code, moex_option_series_code):
    opt_df = moex_options_client.get_option_series_desk(asset_code=moex_asset_code, series_code=moex_option_series_code)
    assert isinstance(opt_df, pd.DataFrame)
    assert len(opt_df) > 0
    assert OptionsTerm.ASSET_CODE in opt_df.columns
    assert OptionsTerm.ASSET_CODE in opt_df.columns
    assert OptionsTerm.EXPIRATION_DATE in opt_df.columns
    assert not opt_df[opt_df[OptionsTerm.ASSET_CODE] == moex_asset_code].empty
