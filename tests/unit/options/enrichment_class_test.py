"""Option enrichment data class tests"""

import pandas as pd
import pytest

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.enrichment_class import OptionsEnrichment


@pytest.fixture(name="opt_enrich")
def fixture_opt_enrich(option_data):
    """Fixture for OptionsEnrichment instance"""
    opt_enr = OptionsEnrichment(option_data)
    return opt_enr


def test_option_enrichment_class_init(option_data):
    opt_enr = OptionsEnrichment(option_data)
    assert isinstance(opt_enr, OptionsEnrichment)


def test__prepare_order_of_columns_enrichment(opt_enrich):
    columns_to_enrich = [OptionsTerm.TIMED_VALUE, OptionsTerm.INTRINSIC_VALUE, OptionsTerm.PRICE_STATUS]
    columns = opt_enrich._prepare_order_of_columns_enrichment(columns_to_enrich)
    assert columns == [
        OptionsTerm.UNDERLYING_PRICE,
        OptionsTerm.INTRINSIC_VALUE,
        OptionsTerm.TIMED_VALUE,
        OptionsTerm.PRICE_STATUS,
    ]


def test_option_enrichment_get_joint_option_with_future(opt_enrich):
    if OptionsTerm.UNDERLYING_PRICE in opt_enrich.data.df_hist.columns:
        opt_enrich.data.df_hist.drop(columns=OptionsTerm.UNDERLYING_PRICE, inplace=True)
    assert OptionsTerm.UNDERLYING_PRICE not in opt_enrich.data.df_hist.columns
    df_opt = opt_enrich.enrich_options(OptionsTerm.UNDERLYING_PRICE)
    assert isinstance(df_opt, pd.DataFrame)
    assert OptionsTerm.UNDERLYING_PRICE in df_opt.columns


def test_option_enrichment_add_future(opt_enrich):
    if OptionsTerm.UNDERLYING_PRICE in opt_enrich.data.df_hist.columns:
        opt_enrich.data.df_hist.drop(columns=[OptionsTerm.UNDERLYING_PRICE], inplace=True)
    assert OptionsTerm.UNDERLYING_PRICE not in opt_enrich.data.df_hist.columns
    res = opt_enrich.add_column(OptionsTerm.UNDERLYING_PRICE)
    assert isinstance(res, OptionsEnrichment)
    assert isinstance(opt_enrich.data.df_hist, pd.DataFrame)
    assert OptionsTerm.UNDERLYING_PRICE in opt_enrich.data.df_hist.columns


def test_option_enrichment_add_intrinsic_and_time_value(opt_enrich):
    assert OptionsTerm.INTRINSIC_VALUE not in opt_enrich.data.df_hist.columns
    res = opt_enrich.add_column(OptionsTerm.INTRINSIC_VALUE)
    assert isinstance(res, OptionsEnrichment)
    assert isinstance(opt_enrich.data.df_hist, pd.DataFrame)
    assert OptionsTerm.INTRINSIC_VALUE in opt_enrich.data.df_hist.columns
    assert OptionsTerm.TIMED_VALUE in opt_enrich.data.df_hist.columns


def test_add_atm_itm_otm(opt_enrich):
    assert OptionsTerm.PRICE_STATUS not in opt_enrich.data.df_hist.columns
    opt_enrich.data.df_hist = opt_enrich.data.df_hist.iloc[-10_000:]
    res = opt_enrich.add_column(OptionsTerm.PRICE_STATUS)
    assert isinstance(res, OptionsEnrichment)
    assert isinstance(opt_enrich.data.df_hist, pd.DataFrame)
    assert OptionsTerm.PRICE_STATUS in opt_enrich.data.df_hist.columns
