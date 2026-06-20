"""Driftless log random-walk price baseline (T27).

``ln S_{t+h} = ln S₀ + Σ r_i``, ``r_i ~ N(0, σ²·dt)`` — zero log-drift (ν = 0), vol estimated from
the sample variance of log returns. The honest no-view baseline: terminal median = ``S₀``.

# 4VERIFY (owner, D2): ν = 0 in log space, σ²_ann = var(r)/dt, sdlog = σ·√H, meanlog = ln S₀.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import ForecastModel, ForecastTarget
from alphavar.options.lib.forecast.price._lognormal import LogNormalPrice


class RandomWalkPrice(ForecastModel):
    """Driftless log random walk; log-normal terminal price (analytic + MC)."""

    name = "random_walk"
    target = ForecastTarget.PRICE
    supports = frozenset({"analytic", "montecarlo"})

    def fit(self, prices: np.ndarray, dt_years: float, horizon_years: float) -> LogNormalPrice:
        returns, spot = self._log_returns(prices)
        sigma2_ann = self._step_var(returns) / dt_years
        sdlog = np.sqrt(sigma2_ann * horizon_years)
        meanlog = np.log(spot)  # ν = 0
        return LogNormalPrice(self.name, spot, horizon_years, meanlog, sdlog)
