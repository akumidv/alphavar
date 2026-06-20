"""Money status data enrichment tests"""

import datetime

import pandas as pd
import pytest

from alphavar.options.dictionary import OptionsPriceStatus, OptionsTerm
from alphavar.options.lib.enrichment import price


def test_add_intrinsic_and_time_value(df_opt_hist):
    df_opt_ext = price.add_intrinsic_and_time_value(df_opt_hist)
    assert isinstance(df_opt_ext, pd.DataFrame)
    assert OptionsTerm.INTRINSIC_VALUE in df_opt_ext.columns
    assert OptionsTerm.TIMED_VALUE in df_opt_ext.columns


def test_add_atm_itm_otm(df_opt_hist):
    dt_filter = df_opt_hist[OptionsTerm.TIMESTAMP].max() - datetime.timedelta(days=10)
    df_opt_ext = price.add_atm_itm_otm_by_chain(df_opt_hist[df_opt_hist[OptionsTerm.TIMESTAMP] > dt_filter])
    assert isinstance(df_opt_ext, pd.DataFrame)
    assert OptionsTerm.PRICE_STATUS in df_opt_ext.columns
    assert not df_opt_ext[df_opt_ext[OptionsTerm.PRICE_STATUS] == OptionsPriceStatus.ATM.code].empty


@pytest.mark.skip("Developing")
def test_add_atm_itm_otm_exp(df_opt_hist):
    dt_filter = df_opt_hist[OptionsTerm.TIMESTAMP].max() - datetime.timedelta(days=10)
    df_opt_ext = price.add_atm_itm_otm_exp(df_opt_hist[df_opt_hist[OptionsTerm.TIMESTAMP] > dt_filter])
    assert isinstance(df_opt_ext, pd.DataFrame)
    assert OptionsTerm.PRICE_STATUS in df_opt_ext.columns
    assert not df_opt_ext[df_opt_ext[OptionsTerm.PRICE_STATUS] == OptionsPriceStatus.ATM.code].empty
