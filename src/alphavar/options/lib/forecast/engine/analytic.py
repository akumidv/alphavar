"""Analytic engine — the model's closed-form terminal distribution → quantiles (T27)."""
from __future__ import annotations

from alphavar.options.lib.forecast._base import FittedProcess, ForecastEngine, ForecastResult


class AnalyticEngine(ForecastEngine):
    """Wrap a fitted process's closed-form terminal distribution as a ``ForecastResult``."""

    name = "analytic"

    def run(self, fitted: FittedProcess) -> ForecastResult:
        dist = fitted.analytic_terminal()
        if dist is None:
            raise ValueError(
                f"model {fitted.model_name!r} has no closed-form terminal distribution; "
                "use engine='montecarlo'"
            )
        return ForecastResult(
            target=fitted.target,
            model=fitted.model_name,
            engine=self.name,
            horizon_years=fitted.horizon_years,
            spot=fitted.spot,
            distribution=dist,
        )
