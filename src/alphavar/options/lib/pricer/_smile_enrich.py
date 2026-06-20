"""DataFrame-level smile fitting: market IVs → an arbitrage-checked model ``iv`` (T21, R5).

Each option slice — fixed ``(asset_code, expiration_date, timestamp)`` — is fit in
log-moneyness ``k = ln(strike / underlying_price)`` with a chosen smile model (default SVI),
and the fitted curve is sampled back at every strike to give our model ``iv``. Pairing this
with ``add_fair_price`` makes ``price``/``iv`` a smooth, arbitrage-checked model output rather
than a per-strike mirror of the venue marks (the T23.6 interim).

# 4VERIFY (owner, D2): the log-moneyness convention (k = ln(K/F), F = underlying_price), the
# per-slice grouping, and that the model ``iv`` is the smile sampled at each strike.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.pricer.smile import SmileResult, make_smile_model
from alphavar.options.lib.pricer.smile._base import SmileModel

_SLICE_KEYS = [OptionsTerm.ASSET_CODE, OptionsTerm.EXPIRATION_DATE, OptionsTerm.TIMESTAMP]


def _slice_keys(df: pd.DataFrame) -> list[str]:
    """Slice grouping keys present in ``df`` (expiration + timestamp are the minimum)."""
    keys = [c for c in _SLICE_KEYS if c in df.columns]
    if OptionsTerm.EXPIRATION_DATE not in keys or OptionsTerm.TIMESTAMP not in keys:
        raise KeyError(f"smile fit needs {OptionsTerm.EXPIRATION_DATE} and {OptionsTerm.TIMESTAMP} columns")
    return keys


def fit_smile_slices(
    df: pd.DataFrame,
    model: str | SmileModel = "svi",
    market_iv_col: str = OptionsTerm.EXCH_MARK_IV,
) -> dict[tuple, SmileResult]:
    """Fit one smile per ``(asset, expiration, timestamp)`` slice; return ``{key: SmileResult}``.

    ``k = ln(strike / underlying_price)``; the slice's expiry ``t`` is taken from the first row's
    ``years_to_expiry``. Slices with no usable point are skipped.
    """
    from alphavar.options.lib.pricer._enrich import years_to_expiry  # local: avoid import cycle

    smile = make_smile_model(model)
    keys = _slice_keys(df)
    results: dict[tuple, SmileResult] = {}
    for key, slice_df in df.groupby(keys, sort=False):
        forward = slice_df[OptionsTerm.UNDERLYING_PRICE].to_numpy(dtype=float)
        strike = slice_df[OptionsTerm.STRIKE].to_numpy(dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            k = np.log(strike / forward)
        iv = slice_df[market_iv_col].to_numpy(dtype=float)
        t = float(
            years_to_expiry(slice_df[OptionsTerm.EXPIRATION_DATE], slice_df[OptionsTerm.TIMESTAMP]).iloc[0]
        )
        results[key if isinstance(key, tuple) else (key,)] = smile.fit(k, iv, t)
    return results


def add_smile_iv(
    df: pd.DataFrame,
    model: str | SmileModel = "svi",
    market_iv_col: str = OptionsTerm.EXCH_MARK_IV,
    out_col: str = OptionsTerm.IV,
) -> pd.DataFrame:
    """Add ``out_col`` = the fitted smile sampled at each option's strike (model IV).

    Needs ``strike``, ``underlying_price``, ``expiration_date``, ``timestamp`` and a market-IV
    column to fit (default the venue ``exch_mark_iv``). Use ``add_model_iv`` first if no market
    IV is stored.
    """
    if market_iv_col not in df.columns:
        raise KeyError(f"smile fit needs a market-IV column {market_iv_col!r} (run add_model_iv first)")
    keys = _slice_keys(df)
    df = df.copy()
    out = np.full(len(df), np.nan, dtype=float)
    positions = {idx: i for i, idx in enumerate(df.index)}
    smile = make_smile_model(model)

    from alphavar.options.lib.pricer._enrich import years_to_expiry

    for _key, slice_df in df.groupby(keys, sort=False):
        forward = slice_df[OptionsTerm.UNDERLYING_PRICE].to_numpy(dtype=float)
        strike = slice_df[OptionsTerm.STRIKE].to_numpy(dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            k = np.log(strike / forward)
        iv = slice_df[market_iv_col].to_numpy(dtype=float)
        t = float(years_to_expiry(slice_df[OptionsTerm.EXPIRATION_DATE], slice_df[OptionsTerm.TIMESTAMP]).iloc[0])
        fitted = smile.fit(k, iv, t).iv(k)
        for idx, value in zip(slice_df.index, fitted, strict=True):
            out[positions[idx]] = value
    df[out_col] = out
    return df
