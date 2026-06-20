"""θ-history extraction for smile forecasting — DataFrame in → SVI parameter time series (T27).

For one expiration, fit an SVI smile per timestamp slice (``k = ln(strike / underlying_price)``,
the same convention as ``pricer._smile_enrich``) and stack the calibrated parameters into a
chronological θ history. This is the ``fixed_expiration`` maturity convention: each historical
slice has the tenor it actually had on that date, so the θ series mixes tenors — the iteration-3
baseline (the ``constant_maturity`` alternative interpolates to a fixed tenor first; planned with
iteration 4 / surface).

# 4VERIFY (owner, D2): the per-timestamp SVI fit + θ stacking order (SMILE_PARAM_NAMES), the
# most-populated-expiration default, and the tenor-mixing of fixed_expiration.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.forecast.smile._base import SMILE_PARAM_NAMES
from alphavar.options.lib.pricer.smile import make_smile_model
from alphavar.options.lib.pricer.smile._base import SmileModel


def default_expiration(df_hist: pd.DataFrame) -> pd.Timestamp:
    """The most-populated expiration in the options history (the de-facto liquid smile)."""
    if OptionsTerm.EXPIRATION_DATE not in df_hist.columns:
        raise KeyError(f"smile forecast needs the {OptionsTerm.EXPIRATION_DATE} column")
    counts = df_hist[OptionsTerm.EXPIRATION_DATE].value_counts()
    if counts.empty:
        raise ValueError("no expirations in the options history")
    return pd.Timestamp(counts.idxmax())


def build_theta_history(
    df_hist: pd.DataFrame,
    expiration: pd.Timestamp | None = None,
    smile_model: str | SmileModel = "svi",
    market_iv_col: str = OptionsTerm.EXCH_MARK_IV,
) -> tuple[np.ndarray, pd.DatetimeIndex, pd.Timestamp]:
    """Fit one SVI smile per timestamp of ``expiration`` → ``(theta (T, 5), timestamps, expiration)``.

    ``expiration`` defaults to the most-populated one. Slices are fit in ``k = ln(strike /
    underlying_price)`` against ``market_iv_col``; θ is stacked in ``SMILE_PARAM_NAMES`` order.
    """
    from alphavar.options.lib.pricer._enrich import years_to_expiry  # local: avoid import cycle

    for col in (OptionsTerm.EXPIRATION_DATE, OptionsTerm.TIMESTAMP, OptionsTerm.STRIKE, OptionsTerm.UNDERLYING_PRICE):
        if col not in df_hist.columns:
            raise KeyError(f"smile forecast needs the {col} column")
    if market_iv_col not in df_hist.columns:
        raise KeyError(f"smile forecast needs a market-IV column {market_iv_col!r} (run add_model_iv first)")

    expiration = default_expiration(df_hist) if expiration is None else pd.Timestamp(expiration)
    df = df_hist[df_hist[OptionsTerm.EXPIRATION_DATE] == expiration]
    if len(df) == 0:
        raise ValueError(f"no option rows for expiration {expiration!r}")

    smile = make_smile_model(smile_model)
    thetas: list[np.ndarray] = []
    times: list[pd.Timestamp] = []
    for ts, slice_df in df.groupby(OptionsTerm.TIMESTAMP, sort=True):
        forward = slice_df[OptionsTerm.UNDERLYING_PRICE].to_numpy(dtype=float)
        strike = slice_df[OptionsTerm.STRIKE].to_numpy(dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            k = np.log(strike / forward)
        iv = slice_df[market_iv_col].to_numpy(dtype=float)
        t = float(years_to_expiry(slice_df[OptionsTerm.EXPIRATION_DATE], slice_df[OptionsTerm.TIMESTAMP]).iloc[0])
        params = smile.fit(k, iv, t).params
        thetas.append(np.array([params[name] for name in SMILE_PARAM_NAMES], dtype=float))
        times.append(pd.Timestamp(ts))

    if len(thetas) < 2:
        raise ValueError(f"need at least 2 timestamps for expiration {expiration!r}; got {len(thetas)}")
    return np.vstack(thetas), pd.DatetimeIndex(times), expiration
