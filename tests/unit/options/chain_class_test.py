"""Option chain data class tests"""

import datetime

import pandas as pd
import pytest

from alphavar.options.chain_class import OptionsChain
from alphavar.options.dictionary import OptionsTerm


@pytest.fixture(name="opt_chain")
def fixture_opt_chain(option_data):
    """Fixture for OptionsChain instance"""
    opt_enr = OptionsChain(option_data)
    return opt_enr


def test_option_chain_class_init(option_data):
    opt_enr = OptionsChain(option_data)
    assert isinstance(opt_enr, OptionsChain)


def test_select_chain(opt_chain):
    assert opt_chain._data.df_chain is None
    df_opt_chain = opt_chain.select_chain()
    assert isinstance(df_opt_chain, pd.DataFrame)
    opt_chain.validate_chain(df_opt_chain)


def test_getter_option_chain(opt_chain):
    assert opt_chain._data.df_chain is None
    df_opt_chain = opt_chain.df_chain
    assert isinstance(df_opt_chain, pd.DataFrame)
    opt_chain.validate_chain(df_opt_chain)


def test_get_settlement_and_expiration_date(opt_chain):
    opt_chain.select_chain()
    settlement_date, expiration_date = opt_chain.get_settlement_and_expiration_date()
    assert isinstance(settlement_date, datetime.date)
    assert isinstance(expiration_date, datetime.date)


def test_get_desk(opt_chain):
    opt_chain.select_chain()
    df_desk = opt_chain.get_desk()
    assert isinstance(df_desk, pd.DataFrame)
    assert OptionsTerm.PRICE + "_call" in df_desk.columns
    assert OptionsTerm.PRICE + "_put" in df_desk.columns
