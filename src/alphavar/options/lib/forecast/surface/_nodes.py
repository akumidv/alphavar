"""Constant-maturity θ-node history for surface forecasting (T27 iteration 4, R5).

The surface state is a stack of SVI parameter vectors at **fixed tenor nodes** (e.g. 7/30/60/90d).
At each timestamp we fit a smile per expiration, interpolate the total variance across expirations
to each node tenor (``_interpolate``), refit SVI to that constant-maturity slice, and stack the node
θ's into one vector. Over time this gives a stacked-θ history a forecast model (RW / VAR / PCA) runs
on directly — and, unlike the ``fixed_expiration`` smile convention, the tenor of each node is held
constant, so the modelled dynamics are not contaminated by tenor roll-down.

# 4VERIFY (owner, D2): the per-timestamp expiration fits → constant-maturity interpolation → SVI
# refit per node, and the node stacking order (node-major, SMILE_PARAM_NAMES within each node).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.forecast.smile._base import SMILE_PARAM_NAMES
from alphavar.options.lib.forecast.surface._interpolate import constant_maturity_iv
from alphavar.options.lib.pricer.smile import make_smile_model
from alphavar.options.lib.pricer.smile._base import SmileModel

_DAYS_PER_YEAR = 365.0
# Default constant-maturity tenor grid (calendar years): 1w / 2w / 1m / 2m / 3m.
DEFAULT_TENOR_NODES = np.array([7.0, 14.0, 30.0, 60.0, 90.0]) / _DAYS_PER_YEAR
_FIT_K_GRID = np.linspace(-0.6, 0.6, 21)
_MIN_STRIKES = 5


def _timestamp_smiles(slice_df: pd.DataFrame, smile: SmileModel, market_iv_col: str) -> dict[float, object]:
    """Fit one smile per expiration present at a single timestamp → ``{tenor: SmileResult}``."""
    from alphavar.options.lib.pricer._enrich import years_to_expiry  # local: avoid import cycle

    smiles: dict[float, object] = {}
    for _exp, exp_df in slice_df.groupby(OptionsTerm.EXPIRATION_DATE, sort=True):
        if len(exp_df) < _MIN_STRIKES:
            continue
        forward = exp_df[OptionsTerm.UNDERLYING_PRICE].to_numpy(dtype=float)
        strike = exp_df[OptionsTerm.STRIKE].to_numpy(dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            k = np.log(strike / forward)
        iv = exp_df[market_iv_col].to_numpy(dtype=float)
        t = float(years_to_expiry(exp_df[OptionsTerm.EXPIRATION_DATE], exp_df[OptionsTerm.TIMESTAMP]).iloc[0])
        if t > 0.0:
            smiles[t] = smile.fit(k, iv, t)
    return smiles


def constant_maturity_theta_history(
    df_hist: pd.DataFrame,
    tenor_nodes: np.ndarray,
    smile_model: str | SmileModel = "svi",
    market_iv_col: str = OptionsTerm.EXCH_MARK_IV,
) -> tuple[np.ndarray, pd.DatetimeIndex, np.ndarray]:
    """Stacked constant-maturity θ history → ``(theta (T, n_nodes*5), timestamps, tenor_nodes)``.

    At each timestamp the surface is read at every ``tenor_nodes`` value (interpolated in total
    variance) and refit to SVI; the node θ's are concatenated node-major. Timestamps that cannot
    produce at least one expiration smile are skipped.
    """
    for col in (OptionsTerm.EXPIRATION_DATE, OptionsTerm.TIMESTAMP, OptionsTerm.STRIKE, OptionsTerm.UNDERLYING_PRICE):
        if col not in df_hist.columns:
            raise KeyError(f"surface forecast needs the {col} column")
    if market_iv_col not in df_hist.columns:
        raise KeyError(f"surface forecast needs a market-IV column {market_iv_col!r} (run add_model_iv first)")

    tenor_nodes = np.asarray(tenor_nodes, dtype=float)
    smile = make_smile_model(smile_model)
    rows: list[np.ndarray] = []
    times: list[pd.Timestamp] = []
    for ts, slice_df in df_hist.groupby(OptionsTerm.TIMESTAMP, sort=True):
        smiles = _timestamp_smiles(slice_df, smile, market_iv_col)
        if not smiles:
            continue
        node_thetas = []
        for tau in tenor_nodes:
            iv_node = constant_maturity_iv(smiles, _FIT_K_GRID, float(tau))
            params = smile.fit(_FIT_K_GRID, iv_node, float(tau)).params
            node_thetas.append(np.array([params[name] for name in SMILE_PARAM_NAMES], dtype=float))
        rows.append(np.concatenate(node_thetas))
        times.append(pd.Timestamp(ts))

    if len(rows) < 2:
        raise ValueError(f"need at least 2 timestamps with a fittable surface; got {len(rows)}")
    return np.vstack(rows), pd.DatetimeIndex(times), tenor_nodes
