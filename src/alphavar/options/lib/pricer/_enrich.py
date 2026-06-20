"""DataFrame-level pricing enrichment (Black-76) — pure functions (T21 / R3).

Derives our model columns from quote rows: ``iv`` (implied vol of a market/mark price under
our Black-76 model) and ``price`` (fair price from a vol). Forward ``F`` is
``underlying_price`` (the future), so the option's tenor is the time to its **own**
expiration.

# 4VERIFY (owner, D2): the year-fraction convention (ACT/365, expiration − timestamp) and
# wiring of df columns into the Black-76 functions. The math itself is in black_scholes.py.
"""
import pandas as pd

from alphavar.options.dictionary import OptionRight, OptionsTerm
from alphavar.options.lib.pricer.black_scholes import bs_forward_price, implied_vol

_DAYS_PER_YEAR = 365.0


def years_to_expiry(expiration: pd.Series, timestamp: pd.Series) -> pd.Series:
    """ACT/365 time to expiry, in years (≥ 0), from two tz-aware timestamp columns."""
    seconds = (expiration - timestamp).dt.total_seconds()
    return (seconds / (_DAYS_PER_YEAR * 86400.0)).clip(lower=0.0)


def add_model_iv(
    df: pd.DataFrame,
    market_col: str = OptionsTerm.EXCH_MARK_PRICE,
    out_col: str = OptionsTerm.IV,
    rate: float = 0.0,
) -> pd.DataFrame:
    """Add ``out_col`` = implied vol (our Black-76) of ``market_col``, per option row.

    Needs: expiration_date, timestamp, underlying_price (forward), strike, option_right.
    Rows whose market price is outside the no-arbitrage bracket get NaN (see ``implied_vol``).
    """
    t_years = years_to_expiry(df[OptionsTerm.EXPIRATION_DATE], df[OptionsTerm.TIMESTAMP])
    is_call = df[OptionsTerm.OPTION_RIGHT] == OptionRight.CALL.value
    df = df.copy()
    df[out_col] = implied_vol(
        df[market_col].to_numpy(dtype=float),
        df[OptionsTerm.UNDERLYING_PRICE].to_numpy(dtype=float),
        df[OptionsTerm.STRIKE].to_numpy(dtype=float),
        t_years.to_numpy(dtype=float),
        is_call.to_numpy(dtype=bool),
        rate,
    )
    return df


def add_fair_price(
    df: pd.DataFrame,
    vol_col: str = OptionsTerm.IV,
    out_col: str = OptionsTerm.PRICE,
    rate: float = 0.0,
) -> pd.DataFrame:
    """Add ``out_col`` = Black-76 fair price from the vol in ``vol_col``, per option row."""
    t_years = years_to_expiry(df[OptionsTerm.EXPIRATION_DATE], df[OptionsTerm.TIMESTAMP])
    is_call = df[OptionsTerm.OPTION_RIGHT] == OptionRight.CALL.value
    df = df.copy()
    df[out_col] = bs_forward_price(
        df[OptionsTerm.UNDERLYING_PRICE].to_numpy(dtype=float),
        df[OptionsTerm.STRIKE].to_numpy(dtype=float),
        t_years.to_numpy(dtype=float),
        df[vol_col].to_numpy(dtype=float),
        is_call.to_numpy(dtype=bool),
        rate,
    )
    return df
