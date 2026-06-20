"""Price values corrections"""

import pandas as pd

from alphavar.options.dictionary import OptionsTerm


def fill_option_price(df: pd.DataFrame, out_col: str = OptionsTerm.EXCH_PRICE) -> pd.DataFrame:
    """Derive the venue's representative traded/quoted price into ``out_col`` (R4.2: this is
    the exchange value → ``exch_price`` by default, NOT our model ``price``).

    out_col =
        - last
        - or avg bid/ask
        - or avg bid/high
        - or avg low/ask
        - or avg low/high
        - or any if only one present of ask, bid, high, low
    """
    if out_col in df.columns and df[out_col].notnull().all():
        return df
    price_col = f"__{out_col}"
    if OptionsTerm.LAST in df.columns:
        df[price_col] = df[OptionsTerm.LAST]
    else:
        df[price_col] = pd.NA
    if OptionsTerm.ASK in df.columns and OptionsTerm.BID in df.columns and df[price_col].isnull().any():
        mid_price_col = f"__mid_{OptionsTerm.PRICE}"
        low_price_col = f"__low_{OptionsTerm.PRICE}"
        df[mid_price_col] = df[OptionsTerm.ASK]
        df[low_price_col] = df[OptionsTerm.BID]
        if OptionsTerm.HIGH in df.columns:
            # df[mid_price_col].fillna(df[OptionsTerm.HIGH], inplace=True)
            df.fillna(value={mid_price_col: df[OptionsTerm.HIGH]}, inplace=True)
        if OptionsTerm.LOW in df.columns:
            # df[low_price_col].fillna(df[OptionsTerm.LOW], inplace=True)
            df.fillna(value={low_price_col: df[OptionsTerm.LOW]}, inplace=True)
        # df[mid_price_col].fillna(df[low_price_col], inplace=True)
        df.fillna(value={mid_price_col: df[low_price_col]}, inplace=True)
        # df[low_price_col].fillna(df[mid_price_col], inplace=True)
        df.fillna(value={low_price_col: df[mid_price_col]}, inplace=True)
        df.loc[:, mid_price_col] = df.loc[:, [mid_price_col, low_price_col]].mean(axis="columns")
        # df[price_col].fillna(df[mid_price_col], inplace=True)
        df.fillna(value={price_col: df[mid_price_col]}, inplace=True)
        df.drop(columns=[mid_price_col, low_price_col], inplace=True)
    if out_col in df.columns:
        # Note: avoid chained inplace assignment (pandas 3.0 SettingWithCopy) — prefer
        # df[col] = df[col].method(value). Prior attempt:
        # df = df[out_col].fillna(df[price_col]).drop(columns=price_col)
        df = df.fillna(value={out_col: df[price_col]}).drop(columns=price_col)
    else:
        df.rename(columns={price_col: out_col}, inplace=True)
    return df


def source_interim_price(
    df: pd.DataFrame, source_col: str = OptionsTerm.EXCH_PRICE, out_col: str = OptionsTerm.PRICE
) -> pd.DataFrame:
    """Interim sourcing of our model ``price`` from the venue ``exch_price`` (R4.2, T23.6).

    # 4VERIFY (owner, D2): until the smile-fit pricer writes a true arbitrage-free model
    # price, our ``price`` mirrors the venue ``exch_price``. Behavior-preserving vs the prior
    # ``fill_option_price``-into-``price`` (the same representative venue price ends up in
    # ``price``); the only change is that it now also lives, explicitly, in ``exch_price``.
    """
    df[out_col] = df[source_col]
    return df
