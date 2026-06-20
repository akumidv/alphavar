"""Shared log-normal terminal price process for the random_walk / gbm models (T27).

``ln S_{t+h} ~ N(meanlog, sdlog²)`` ⇒ ``S_{t+h}`` is log-normal; both an analytic distribution
and Monte-Carlo draws come from the same ``LogNormalTerminal``.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import FittedProcess, ForecastTarget
from alphavar.options.lib.forecast._stats import LogNormalTerminal


class LogNormalPrice(FittedProcess):
    """Calibrated log-normal terminal price (analytic + MC)."""

    def __init__(self, model_name: str, spot: float, horizon_years: float, meanlog: float, sdlog: float):
        self.target = ForecastTarget.PRICE
        self.model_name = model_name
        self.spot = float(spot)
        self.horizon_years = float(horizon_years)
        self._dist = LogNormalTerminal(meanlog, sdlog)

    def analytic_terminal(self) -> LogNormalTerminal:
        return self._dist

    def sample_terminal(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return self._dist.sample(n, rng)
