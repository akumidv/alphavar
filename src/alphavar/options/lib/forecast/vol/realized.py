"""Trailing realized-volatility baseline (T27).

Annualized sample volatility of log returns, held flat over the horizon: ``σ = √(var(r)/dt)``.
The honest no-model baseline for the vol target.

# 4VERIFY (owner, D2): σ = √(var(r)/dt_years) (ACT/365 annualization), constant over the horizon.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import ForecastModel, ForecastTarget
from alphavar.options.lib.forecast.vol._point import PointVol


class RealizedVol(ForecastModel):
    """Trailing annualized realized volatility; analytic point forecast."""

    name = "realized"
    target = ForecastTarget.VOL
    supports = frozenset({"analytic"})

    def fit(self, prices: np.ndarray, dt_years: float, horizon_years: float) -> PointVol:
        returns, _ = self._log_returns(prices)
        vol = float(np.sqrt(self._step_var(returns) / dt_years))
        return PointVol(self.name, vol, horizon_years, ref_vol=vol)
