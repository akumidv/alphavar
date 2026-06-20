"""Desk for chain module tests"""

import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.chain.desk import convert_chain_to_desk


def test_convert_chain_to_desk(df_chain):
    df_desk = convert_chain_to_desk(df_chain)
    assert isinstance(df_desk, pd.DataFrame)
    assert OptionsTerm.PRICE + "_call" in df_desk.columns
    assert OptionsTerm.PRICE + "_put" in df_desk.columns
