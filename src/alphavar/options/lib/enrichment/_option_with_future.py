"""
Add necessary future value to options
"""

import pandas as pd

from alphavar.options.dictionary import OptionsTerm


def join_option_with_future(df_hist: pd.DataFrame, df_fut: pd.DataFrame) -> pd.DataFrame:
    """Join futures column to correspond options"""
    if OptionsTerm.UNDERLYING_PRICE in df_hist.columns:
        df_hist = df_hist.drop(columns=[OptionsTerm.UNDERLYING_PRICE])
    df_fut = df_fut.rename(
        columns={
            OptionsTerm.PRICE: OptionsTerm.UNDERLYING_PRICE,
            OptionsTerm.EXPIRATION_DATE: OptionsTerm.UNDERLYING_EXPIRATION_DATE,
        }
    )
    df_ext_opt = df_hist.merge(df_fut, on=[OptionsTerm.TIMESTAMP, OptionsTerm.UNDERLYING_EXPIRATION_DATE], how="left")
    return df_ext_opt
