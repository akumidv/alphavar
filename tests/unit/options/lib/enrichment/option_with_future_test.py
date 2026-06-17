"""Tests for joining option with futures"""
import pandas as pd

from alphavar.options.dictionary import OptionsColumns as OCl
from alphavar.options.lib.enrichment import join_option_with_future


def test_join_option_future(df_opt_hist, df_fut_hist):
    if OCl.UNDERLYING_PRICE.nm in df_opt_hist.columns:
        df_opt_hist.drop(columns=[OCl.UNDERLYING_PRICE.nm], inplace=True)
    assert OCl.UNDERLYING_PRICE.nm not in df_opt_hist.columns
    df_ext_opt = join_option_with_future(df_opt_hist, df_fut_hist)
    assert isinstance(df_ext_opt, pd.DataFrame)
    assert len(df_ext_opt) == len(df_opt_hist)
    assert OCl.UNDERLYING_PRICE.nm in df_ext_opt.columns
