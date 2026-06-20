"""EWMA (RiskMetrics) volatility forecast (T27).

Exponentially-weighted moving variance ``σ²_t = λ·σ²_{t-1} + (1−λ)·r²_{t-1}`` (default λ = 0.94,
the RiskMetrics daily decay). EWMA has a **flat** forecast term structure (``E[σ²_{t+k}] = σ²_t``),
so the horizon vol is the current EWMA level, annualized.

# 4VERIFY (owner, D2): the EWMA recursion, λ = 0.94 default, the flat term structure, and the
# ACT/365 annualization ``σ = √(σ²_step/dt)``. ``spot`` = trailing realized vol (change reference).
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import ForecastModel, ForecastTarget
from alphavar.options.lib.forecast.vol._point import PointVol

_RISKMETRICS_LAMBDA = 0.94


def ewma_variance(returns: np.ndarray, lam: float) -> float:
    """Current EWMA per-step variance after folding in all returns (seed = sample variance)."""
    var = float(np.var(returns))
    for x in returns:
        var = lam * var + (1.0 - lam) * x * x
    return var


class EwmaVol(ForecastModel):
    """RiskMetrics EWMA volatility; analytic point forecast (flat term structure)."""

    name = "ewma"
    target = ForecastTarget.VOL
    supports = frozenset({"analytic"})

    def __init__(self, lam: float = _RISKMETRICS_LAMBDA):
        self.lam = float(lam)

    def fit(self, prices: np.ndarray, dt_years: float, horizon_years: float) -> PointVol:
        returns, _ = self._log_returns(prices)
        vol = float(np.sqrt(ewma_variance(returns, self.lam) / dt_years))
        ref = float(np.sqrt(self._step_var(returns) / dt_years))
        return PointVol(self.name, vol, horizon_years, ref_vol=ref)
