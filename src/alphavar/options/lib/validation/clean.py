"""Opt-in remediation — the only place validation rewrites data (T21).

Detection (``input_checks``/``model_checks``) is non-mutating; ``clean`` is the explicit,
flag-driven fix step the caller opts into after reading the report.

# 4VERIFY (owner, D2): each fix drops/rewrites rows — defaults are all-off, so nothing
# changes unless asked. Timestamp rounding floors to the timeframe grid (LOCF/labels handled
# upstream by the resampler).
"""
from __future__ import annotations

import pandas as pd

from alphavar.options.dictionary import OptionsTerm, Timeframe
from alphavar.options.lib.validation.input_checks import natural_key


def clean(
    df: pd.DataFrame,
    drop_duplicates: bool = False,
    drop_na_price: bool = False,
    round_timestamp: Timeframe | None = None,
) -> pd.DataFrame:
    """Return a remediated copy of ``df``. All fixes are opt-in (defaults off).

    - ``drop_duplicates`` — keep the last row per natural ``(contract, timestamp)`` key.
    - ``drop_na_price`` — drop rows whose ``price`` is null or ≤ 0.
    - ``round_timestamp`` — floor ``timestamp`` to the given timeframe grid.
    """
    df = df.copy()
    if round_timestamp is not None and OptionsTerm.TIMESTAMP in df.columns:
        df[OptionsTerm.TIMESTAMP] = df[OptionsTerm.TIMESTAMP].dt.floor(round_timestamp.offset)
    if drop_na_price and OptionsTerm.PRICE in df.columns:
        df = df[df[OptionsTerm.PRICE].notna() & (df[OptionsTerm.PRICE] > 0)]
    if drop_duplicates:
        keys = natural_key(df)
        if keys:
            df = df.drop_duplicates(subset=keys, keep="last")
    return df.reset_index(drop=True)
