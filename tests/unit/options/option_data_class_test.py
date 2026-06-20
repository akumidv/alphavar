"""Tests for OptionsData class"""

import pandas as pd

from alphavar.io.provider import PandasLocalFileProvider
from alphavar.options.dictionary import OptionsTerm
from alphavar.options.entities import AssetMeta
from alphavar.options.option_data_class import OptionsData


class _RefProvider:
    """Minimal provider stub that only serves a reference (for the reapply tests)."""

    def __init__(self, asset: AssetMeta | None):
        self._asset = asset

    def load_reference(self, asset_code: str):
        return self._asset, pd.DataFrame()


def test_option_data_class_init(exchange_provider, asset_code):
    opt = OptionsData(exchange_provider, asset_code)
    assert isinstance(opt, OptionsData)


def test_option_data_class_df_opt(exchange_provider, asset_code, provider_params):
    opt = OptionsData(exchange_provider, asset_code, provider_params)
    assert isinstance(opt, OptionsData)
    assert isinstance(opt.df_hist, pd.DataFrame)
    assert all(col in PandasLocalFileProvider.options_columns for col in opt.df_hist.columns)


def test_option_data_class_df_fut(exchange_provider, asset_code, provider_params):
    opt = OptionsData(exchange_provider, asset_code, provider_params)
    assert isinstance(opt, OptionsData)
    assert isinstance(opt.df_fut, pd.DataFrame)
    assert all(col in PandasLocalFileProvider.futures_columns for col in opt.df_fut.columns)


def test_reference_absent_is_none_and_reapply_is_noop(exchange_provider, asset_code):
    # The committed wide fixtures carry no reference layer yet.
    opt = OptionsData(exchange_provider, asset_code)
    assert opt.reference is None
    df = pd.DataFrame({OptionsTerm.PRICE: [1.0, 2.0]})
    pd.testing.assert_frame_equal(opt.reapply_reference(df), df)


def test_reapply_reference_broadcasts_asset_level_constants():
    meta = AssetMeta(asset_code="BTC", instrument_kind="option", currency="USD")
    opt = OptionsData(_RefProvider(meta), "BTC")
    assert opt.reference == meta
    out = opt.reapply_reference(pd.DataFrame({OptionsTerm.PRICE: [1.0, 2.0]}))
    assert (out[OptionsTerm.ASSET_CODE] == "BTC").all()
    assert (out[OptionsTerm.CURRENCY] == "USD").all()
    assert (out[OptionsTerm.INSTRUMENT_KIND] == "option").all()


def test_reapply_reference_does_not_overwrite_present_columns():
    meta = AssetMeta(asset_code="BTC", currency="USD")
    opt = OptionsData(_RefProvider(meta), "BTC")
    # currency already in the frame (a different value) — must be left untouched.
    df = pd.DataFrame({OptionsTerm.PRICE: [1.0], OptionsTerm.CURRENCY: ["RUB"]})
    out = opt.reapply_reference(df)
    assert (out[OptionsTerm.CURRENCY] == "RUB").all()
