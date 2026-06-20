import datetime

import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.chain.chain_selector import (
    get_chain_settlement_and_expiration_date,
    select_chain,
    validate_chain,
)


def test_select_chain(df_opt_hist):
    df_chain = select_chain(df_opt_hist)
    assert isinstance(df_chain, pd.DataFrame)
    assert len(df_chain[OptionsTerm.TIMESTAMP].unique()) == 1
    assert len(df_chain[OptionsTerm.EXPIRATION_DATE].unique()) == 1
    validate_chain(df_chain)


def test_get_chain_datetime_and_expiration_date(df_chain):
    settlement_date, expiration_date = get_chain_settlement_and_expiration_date(df_chain)
    assert isinstance(settlement_date, datetime.date)
    assert isinstance(expiration_date, datetime.date)
