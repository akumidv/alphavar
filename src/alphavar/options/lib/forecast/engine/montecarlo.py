"""Monte-Carlo engine — simulate terminal draws → empirical distribution (T27, default engine)."""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import FittedProcess, ForecastEngine, ForecastResult

_DEFAULT_PATHS = 10000


class MonteCarloEngine(ForecastEngine):
    """Simulate ``n`` terminal values from a fitted process; ``seed`` makes it reproducible."""

    name = "montecarlo"

    def __init__(self, n: int = _DEFAULT_PATHS, seed: int | None = None):
        self.n = int(n)
        self.seed = seed

    def run(self, fitted: FittedProcess) -> ForecastResult:
        rng = np.random.default_rng(self.seed)
        samples = np.asarray(fitted.sample_terminal(self.n, rng), dtype=float)
        return ForecastResult(
            target=fitted.target,
            model=fitted.model_name,
            engine=self.name,
            horizon_years=fitted.horizon_years,
            spot=fitted.spot,
            samples=samples,
        )
