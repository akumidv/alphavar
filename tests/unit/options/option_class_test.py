"""Tests for option class"""
import pandas as pd
import pytest

from alphavar.options.dictionary import OptionsColumns as OCl
from alphavar import Option
from alphavar.io.provider import PandasLocalFileProvider


@pytest.fixture(name='option_instance')
def option_instance_fixture(exchange_provider, option_symbol, provider_params) -> Option:
    """Option instance"""
    opt = Option(exchange_provider, option_symbol, provider_params)
    return opt


def test_option_class_init(exchange_provider, option_symbol):
    opt = Option(exchange_provider, option_symbol)
    assert isinstance(opt, Option)


def test_option_class_df_opt(option_instance):
    assert isinstance(option_instance.df_hist, pd.DataFrame)
    assert all((col in PandasLocalFileProvider.options_columns for col in option_instance.df_hist.columns))


@pytest.mark.xfail(reason="pending T23.6: committed test data predates the current dictionary "
                          "(has exchange_price/exchange_iv); EXCHANGE_MARK_PRICE/IV don't "
                          "exist in it. Needs the dict<->data migration / new logic.",
                   strict=False)
def test_option_class_with_extra_columns(exchange_provider, option_symbol, provider_params):
    columns = PandasLocalFileProvider.options_columns + [OCl.EXCHANGE_MARK_PRICE.nm, OCl.EXCHANGE_MARK_IV.nm]
    opt = Option(exchange_provider, option_symbol, provider_params, option_columns=columns)
    assert isinstance(opt, Option)
    assert isinstance(opt.df_hist, pd.DataFrame)
    assert all((col in opt.df_hist.columns for col in columns))


def test_enrichment_add_future(option_instance):
    df_opt = option_instance.df_hist
    if OCl.UNDERLYING_PRICE.nm in df_opt.columns:
        df_opt.drop(columns=[OCl.UNDERLYING_PRICE.nm], inplace=True)
    assert OCl.UNDERLYING_PRICE.nm not in df_opt.columns
    # option_instance.enrichment.add_future()
    option_instance.enrichment.enrich_options(OCl.UNDERLYING_PRICE)
    df_opt = option_instance.df_hist
    assert isinstance(df_opt, pd.DataFrame)
    assert OCl.UNDERLYING_PRICE.nm in df_opt.columns


@pytest.mark.xfail(reason="pending T19: load_options_chain must load the chain from local "
                          "history (currently NotImplementedError)", strict=False)
def test_chain_select_chain(option_instance):
    df_chain = option_instance.chain.select_chain()
    assert isinstance(df_chain, pd.DataFrame)
    option_instance.chain.validate_chain(df_chain)
