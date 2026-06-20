"""Geometric Brownian motion price model (T27).

Log returns are i.i.d. normal with drift; ``ν = mean(r)/dt`` is the estimated log-return drift
(``μ − ½σ²`` in GBM terms) and ``σ²_ann = var(r)/dt``. Terminal price is log-normal:
``ln S_{t+h} ~ N(ln S₀ + ν·H, σ²·H)``.

# 4VERIFY (owner, D2): ν = mean(r)/dt, σ²_ann = var(r)/dt, sdlog = σ·√H, meanlog = ln S₀ + ν·H.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import ForecastModel, ForecastTarget
from alphavar.options.lib.forecast.price._lognormal import LogNormalPrice


class GbmPrice(ForecastModel):
    """GBM with estimated drift + vol; log-normal terminal price (analytic + MC)."""

    name = "gbm"
    target = ForecastTarget.PRICE
    supports = frozenset({"analytic", "montecarlo"})

    def fit(self, prices: np.ndarray, dt_years: float, horizon_years: float) -> LogNormalPrice:
        returns, spot = self._log_returns(prices)
        nu_ann = float(np.mean(returns)) / dt_years
        sigma2_ann = self._step_var(returns) / dt_years
        meanlog = np.log(spot) + nu_ann * horizon_years
        sdlog = np.sqrt(sigma2_ann * horizon_years)
        return LogNormalPrice(self.name, spot, horizon_years, meanlog, sdlog)
