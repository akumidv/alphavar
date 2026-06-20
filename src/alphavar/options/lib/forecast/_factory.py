"""Forecast factory — pick a model by (target, name) and an engine by name (T27).

Implemented today: target ``price`` (``random_walk`` / ``gbm`` / ``garch`` / ``ar1`` / ``empirical``)
× engines ``analytic`` / ``montecarlo`` / ``bootstrap``. Still-planned **factor-conditional** price
models (``factor_linear`` / ``var``) raise ``NotImplementedError`` — they need an exogenous-factor
input contract (the composable result-chain, ADR 0003), not yet built. See TASKS T27 for the catalog.
"""
from __future__ import annotations

from alphavar.options.lib.forecast._base import ForecastEngine, ForecastModel, ForecastTarget
from alphavar.options.lib.forecast.engine.analytic import AnalyticEngine
from alphavar.options.lib.forecast.engine.bootstrap import BootstrapEngine
from alphavar.options.lib.forecast.engine.montecarlo import MonteCarloEngine
from alphavar.options.lib.forecast.price.ar1 import Ar1Price
from alphavar.options.lib.forecast.price.empirical import EmpiricalPrice
from alphavar.options.lib.forecast.price.garch import GarchPrice
from alphavar.options.lib.forecast.price.gbm import GbmPrice
from alphavar.options.lib.forecast.price.random_walk import RandomWalkPrice
from alphavar.options.lib.forecast.vol.ewma import EwmaVol
from alphavar.options.lib.forecast.vol.garch import GarchVol
from alphavar.options.lib.forecast.vol.har import HarVol
from alphavar.options.lib.forecast.vol.realized import RealizedVol

_PRICE_MODELS: dict[str, type[ForecastModel]] = {
    m.name: m for m in (RandomWalkPrice, GbmPrice, GarchPrice, Ar1Price, EmpiricalPrice)
}
_VOL_MODELS: dict[str, type[ForecastModel]] = {m.name: m for m in (EwmaVol, GarchVol, HarVol, RealizedVol)}
_MODELS: dict[ForecastTarget, dict[str, type[ForecastModel]]] = {
    ForecastTarget.PRICE: _PRICE_MODELS,
    ForecastTarget.VOL: _VOL_MODELS,
}
_ENGINES: dict[str, type[ForecastEngine]] = {
    AnalyticEngine.name: AnalyticEngine,
    MonteCarloEngine.name: MonteCarloEngine,
    BootstrapEngine.name: BootstrapEngine,
}

# Catalogued in TASKS T27 but not yet built — surfaced as NotImplementedError, not "unknown".
# Factor-conditional price models need the exogenous-factor input contract (ADR 0003 result-chain).
_PLANNED_MODELS: dict[ForecastTarget, frozenset[str]] = {ForecastTarget.PRICE: frozenset({"factor_linear", "var"})}
_PLANNED_TARGETS: frozenset[ForecastTarget] = frozenset({ForecastTarget.SURFACE})
# The smile target has a parameter-vector state and a ``SmileForecast`` result, so it lives in its
# own sibling factory (``forecast.smile.make_smile_forecast_model``) rather than this scalar one.
_DEDICATED_TARGETS: frozenset[ForecastTarget] = frozenset({ForecastTarget.SMILE})

DEFAULT_PRICE_MODEL = GbmPrice.name
DEFAULT_VOL_MODEL = EwmaVol.name
DEFAULT_ENGINE = MonteCarloEngine.name


def make_forecast_model(target: ForecastTarget | str, name: str) -> ForecastModel:
    """Model instance for ``(target, name)``; raises on unknown names and planned-but-unbuilt ones."""
    target = ForecastTarget(target)
    if target in _DEDICATED_TARGETS:
        raise NotImplementedError(
            f"target {target.value!r} has a parameter-vector state and a SmileForecast result; "
            "use forecast.smile.make_smile_forecast_model (T27 iteration 3)"
        )
    if target in _PLANNED_TARGETS:
        raise NotImplementedError(f"forecast target {target.value!r} is planned (T27), not yet implemented")
    models = _MODELS[target]
    if name in models:
        return models[name]()
    if name in _PLANNED_MODELS.get(target, frozenset()):
        raise NotImplementedError(f"model {name!r} for target {target.value!r} is planned (T27)")
    raise ValueError(f"unknown {target.value} model {name!r}; available: {sorted(models)}")


def make_engine(name: str = DEFAULT_ENGINE, *, n: int = 10000, seed: int | None = None) -> ForecastEngine:
    """Engine instance by name (``montecarlo`` default; ``analytic`` / ``bootstrap``)."""
    if name == MonteCarloEngine.name:
        return MonteCarloEngine(n=n, seed=seed)
    if name == AnalyticEngine.name:
        return AnalyticEngine()
    if name == BootstrapEngine.name:
        return BootstrapEngine(n=n, seed=seed)
    raise ValueError(f"unknown engine {name!r}; available: {sorted(_ENGINES)}")
