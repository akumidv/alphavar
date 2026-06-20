"""Bootstrap engine — model-free resampling of a process's own history (T27 it.5).

Turns a fitted process into a distribution by calling its ``bootstrap_terminal`` (a moving-block
resample of the historical returns/residuals), not its parametric noise. Only processes that expose
an empirical series support it (today: ``empirical``); others return ``None`` ⇒ a clear error.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import FittedProcess, ForecastEngine, ForecastResult

_DEFAULT_PATHS = 10000


class BootstrapEngine(ForecastEngine):
    """Resample the fitted process's history into ``n`` terminal draws; ``seed`` for reproducibility."""

    name = "bootstrap"

    def __init__(self, n: int = _DEFAULT_PATHS, seed: int | None = None, block: int | None = None):
        self.n = int(n)
        self.seed = seed
        self.block = block

    def run(self, fitted: FittedProcess) -> ForecastResult:
        rng = np.random.default_rng(self.seed)
        draws = fitted.bootstrap_terminal(self.n, rng, self.block)
        if draws is None:
            raise ValueError(
                f"model {fitted.model_name!r} has no empirical series to bootstrap; "
                "use engine='montecarlo' or 'analytic'"
            )
        return ForecastResult(
            target=fitted.target,
            model=fitted.model_name,
            engine=self.name,
            horizon_years=fitted.horizon_years,
            spot=fitted.spot,
            samples=np.asarray(draws, dtype=float),
        )
