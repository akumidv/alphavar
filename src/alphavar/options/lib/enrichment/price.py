"""
Internal realization for option money data enrichment
"""

import pandas as pd

from alphavar.options.dictionary import OptionsPriceStatus, OptionsTerm, OptionsType
from alphavar.options.lib.chain import get_chain_atm_itm_otm


def add_intrinsic_and_time_value(df_hist):
    """
    Adding columns with intrinsic value and time value
    """

    df_hist.loc[:, OptionsTerm.INTRINSIC_VALUE] = 0.0
    df_hist.loc[df_hist[OptionsTerm.OPTION_RIGHT] == OptionsType.CALL.value, OptionsTerm.INTRINSIC_VALUE] = (
        df_hist[OptionsTerm.UNDERLYING_PRICE] - df_hist[OptionsTerm.STRIKE]
    )
    df_hist.loc[df_hist[OptionsTerm.OPTION_RIGHT] == OptionsType.PUT.value, OptionsTerm.INTRINSIC_VALUE] = (
        df_hist[OptionsTerm.STRIKE] - df_hist[OptionsTerm.UNDERLYING_PRICE]
    )
    df_hist.loc[df_hist[OptionsTerm.INTRINSIC_VALUE] < 0, OptionsTerm.INTRINSIC_VALUE] = 0
    df_hist.loc[:, OptionsTerm.TIMED_VALUE] = df_hist[OptionsTerm.PRICE] - df_hist[OptionsTerm.INTRINSIC_VALUE]
    return df_hist


def add_atm_itm_otm_by_chain(df_hist):
    """
    Should be optimized - very slow
    """

    money_col_df = df_hist.groupby([OptionsTerm.TIMESTAMP, OptionsTerm.EXPIRATION_DATE], group_keys=False).apply(
        get_chain_atm_itm_otm, include_groups=False
    )
    df_hist = pd.concat([df_hist, money_col_df], axis="columns")
    return df_hist


def add_atm_itm_otm_exp(df_hist):
    """
    Slower than add_atm_itm_otm_by

    Alternative:
     - 1. Idea to improve change call to 1 and put to -1 and multiple on _diff
     - 2. calc based on intrinsic values. If less 0 - OTM, If greater ITM. Question in atm
       detection - minimal abs intrinsic?.
    """

    df_hist.loc[:, "_diff"] = df_hist[OptionsTerm.UNDERLYING_PRICE] - df_hist[OptionsTerm.STRIKE]
    df_hist.loc[:, "_diff_abs"] = df_hist["_diff"].abs()

    def atm_otm_itm(x):
        atm_strikes = x[x["_diff_abs"] == x["_diff_abs"].min()]
        atm_strike_diff = atm_strikes.iloc[0]["_diff"]

        if x.iloc[0][OptionsTerm.OPTION_RIGHT] == OptionsType.CALL.value:
            itm = x[x["_diff"] > atm_strike_diff]
            otm = x[x["_diff"] < atm_strike_diff]
            return pd.Series(
                [OptionsPriceStatus.ITM.code] * len(itm)
                + [OptionsPriceStatus.ATM.code]
                + [OptionsPriceStatus.OTM.code] * len(otm)
            )
        itm = x[x["_diff"] < atm_strike_diff]
        otm = x[x["_diff"] > atm_strike_diff]
        return pd.Series(
            [OptionsPriceStatus.OTM.code] * len(otm)
            + [OptionsPriceStatus.ATM.code]
            + [OptionsPriceStatus.ITM.code] * len(itm)
        )

    df_hist.loc[:, OptionsTerm.PRICE_STATUS] = (
        df_hist.sort_values(
            by=[OptionsTerm.TIMESTAMP, OptionsTerm.EXPIRATION_DATE, OptionsTerm.OPTION_RIGHT, OptionsTerm.STRIKE]
        )
        .groupby([OptionsTerm.TIMESTAMP, OptionsTerm.EXPIRATION_DATE, OptionsTerm.OPTION_RIGHT], group_keys=False)[
            ["_diff", "_diff_abs", OptionsTerm.OPTION_RIGHT]
        ]
        .apply(atm_otm_itm, include_groups=False)
        .drop(columns=["_diff"])
        .reset_index(drop=True)
    )
    return df_hist
