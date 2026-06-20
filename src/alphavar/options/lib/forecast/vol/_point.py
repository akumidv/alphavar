"""Point (deterministic) volatility forecast as a degenerate terminal distribution (T27).

EWMA / realized / HAR produce a single conditional vol for the horizon; wrapping it as a
``DegenerateTerminal`` lets it flow through the same engines / ``ForecastResult`` as the
distributional models. ``spot`` carries the trailing realized vol as the change-view reference.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import FittedProcess, ForecastTarget
from alphavar.options.lib.forecast._stats import DegenerateTerminal


class PointVol(FittedProcess):
    """A deterministic horizon vol forecast (analytic point); ``spot`` = trailing realized vol."""

    def __init__(self, model_name: str, vol: float, horizon_years: float, ref_vol: float):
        self.target = ForecastTarget.VOL
        self.model_name = model_name
        self.spot = float(ref_vol)
        self.horizon_years = float(horizon_years)
        self._dist = DegenerateTerminal(vol)

    def analytic_terminal(self) -> DegenerateTerminal:
        return self._dist

    def sample_terminal(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return self._dist.sample(n, rng)
