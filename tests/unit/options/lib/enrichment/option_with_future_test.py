"""Tests for joining option with futures"""

import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.enrichment import join_option_with_future


def test_join_option_future(df_opt_hist, df_fut_hist):
    if OptionsTerm.UNDERLYING_PRICE in df_opt_hist.columns:
        df_opt_hist.drop(columns=[OptionsTerm.UNDERLYING_PRICE], inplace=True)
    assert OptionsTerm.UNDERLYING_PRICE not in df_opt_hist.columns
    df_ext_opt = join_option_with_future(df_opt_hist, df_fut_hist)
    assert isinstance(df_ext_opt, pd.DataFrame)
    assert len(df_ext_opt) == len(df_opt_hist)
    assert OptionsTerm.UNDERLYING_PRICE in df_ext_opt.columns
