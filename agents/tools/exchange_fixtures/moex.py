"""MOEX fixture recording — declares which MOEX ISS calls to capture.

Reuses the real `alphavar.exchange.moex` API. Asset `SI` matches the test fixtures
(conftest `moex_asset_code`); the option series code is discovered from the live response.
"""
from alphavar.exchange._abstract_exchange import RequestClass
from alphavar.exchange.moex import MoexExchange, MoexOptions, MoexAssetType
from alphavar.options_lib.dictionary import OptionsColumns as OCl

from agents.tools.exchange_fixtures._record import record, try_call

ASSET = 'SI'


def _drive(make_spy):
    client = make_spy(RequestClass(api_url=MoexExchange.PRODUCT_API_URL))
    market = MoexOptions(client)
    try_call('get_assets', market.get_assets)
    # get_assets_list(FUTURES/OPTIONS) filters get_assets by asset_type -> distinct
    # query keys the tests need.
    try_call('get_assets futures', lambda: market.get_assets(asset_type=MoexAssetType.FUTURES))
    try_call('get_asset_info',
             lambda: market.get_asset_info(asset_code=ASSET, asset_type=MoexAssetType.FUTURES))
    try_call('get_asset_futures', lambda: market.get_asset_futures(asset_code=ASSET))
    try_call('get_asset_options', lambda: market.get_asset_options(asset_code=ASSET))
    try_call('get_asset_options AFLT', lambda: market.get_asset_options(asset_code='AFLT'))
    series = try_call('get_option_series', lambda: market.get_option_series(asset_code=ASSET))
    if series is not None and len(series):
        series_code = series.iloc[0][OCl.SERIES_CODE.nm]
        try_call('get_option_series_list',
                 lambda: market.get_option_series_list(asset_code=ASSET, series_code=series_code))
        try_call('get_option_series_desk',
                 lambda: market.get_option_series_desk(asset_code=ASSET, series_code=series_code))


def run():
    record('moex', _drive)
