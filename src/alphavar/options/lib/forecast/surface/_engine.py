"""Surface-forecast engines — a fitted stacked-θ process → a ``SurfaceForecast`` (T27 it.4).

The same two-engine axis as smile/scalar forecasts: ``analytic`` decodes the expected stacked θ into
the expected surface; ``montecarlo`` draws stacked-θ scenarios from ``N(mean, cov)`` → σ(k,τ) bands.
The stacked-θ process is the verified smile ``ThetaProcess`` (Gaussian terminal) on a longer vector.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast.smile._base import ThetaProcess
from alphavar.options.lib.forecast.surface._base import SurfaceForecast

_DEFAULT_PATHS = 10000


class SurfaceAnalyticEngine:
    """Expected surface from the mean terminal stacked θ (no scenarios)."""

    name = "analytic"

    def __init__(self, tenor_nodes: np.ndarray):
        self.tenor_nodes = np.asarray(tenor_nodes, dtype=float)

    def run(self, fitted: ThetaProcess) -> SurfaceForecast:
        return SurfaceForecast(
            model=fitted.model_name,
            engine=self.name,
            tenor_nodes=self.tenor_nodes,
            horizon_years=fitted.horizon_years,
            mean_theta=fitted.mean_terminal_theta(),
            samples=None,
        )


class SurfaceMonteCarloEngine:
    """Draw ``n`` stacked-θ scenarios → σ(k,τ) quantile bands; ``seed`` reproducible."""

    name = "montecarlo"

    def __init__(self, tenor_nodes: np.ndarray, n: int = _DEFAULT_PATHS, seed: int | None = None):
        self.tenor_nodes = np.asarray(tenor_nodes, dtype=float)
        self.n = int(n)
        self.seed = seed

    def run(self, fitted: ThetaProcess) -> SurfaceForecast:
        rng = np.random.default_rng(self.seed)
        samples = fitted.sample_terminal_theta(self.n, rng)
        return SurfaceForecast(
            model=fitted.model_name,
            engine=self.name,
            tenor_nodes=self.tenor_nodes,
            horizon_years=fitted.horizon_years,
            mean_theta=fitted.mean_terminal_theta(),
            samples=samples,
        )
