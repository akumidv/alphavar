"""Smile-forecast engines — a fitted θ process → a ``SmileForecast`` (T27 iteration 3).

The same two-engine axis as the scalar forecast: ``analytic`` presents the expected smile from the
mean terminal θ (no scenario bands); ``montecarlo`` draws θ scenarios from ``N(mean, cov)`` so the
result carries σ(k) quantile bands. Separate from the scalar engines only because the result type
differs (``SmileForecast`` vs ``ForecastResult``).
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast.smile._base import SmileForecast, ThetaProcess

_DEFAULT_PATHS = 10000


class SmileAnalyticEngine:
    """Expected smile from the mean terminal θ (no scenarios)."""

    name = "analytic"

    def run(self, fitted: ThetaProcess) -> SmileForecast:
        return SmileForecast(
            model=fitted.model_name,
            engine=self.name,
            param_names=fitted.param_names,
            t_target=fitted.t_target,
            horizon_years=fitted.horizon_years,
            theta0=fitted.theta0,
            mean_theta=fitted.mean_terminal_theta(),
            samples=None,
        )


class SmileMonteCarloEngine:
    """Draw ``n`` θ scenarios from the terminal Gaussian → σ(k) quantile bands; ``seed`` reproducible."""

    name = "montecarlo"

    def __init__(self, n: int = _DEFAULT_PATHS, seed: int | None = None):
        self.n = int(n)
        self.seed = seed

    def run(self, fitted: ThetaProcess) -> SmileForecast:
        rng = np.random.default_rng(self.seed)
        samples = fitted.sample_terminal_theta(self.n, rng)
        return SmileForecast(
            model=fitted.model_name,
            engine=self.name,
            param_names=fitted.param_names,
            t_target=fitted.t_target,
            horizon_years=fitted.horizon_years,
            theta0=fitted.theta0,
            mean_theta=fitted.mean_terminal_theta(),
            samples=samples,
        )
