"""Smile-forecast factory — pick a θ model / engine / maturity convention by name (T27).

A sibling of the scalar ``forecast._factory`` and of ``pricer.smile.make_smile_model`` (ADR 0002):
the smile target's state is a parameter vector and its result is a ``SmileForecast``, so it has its
own factory. Models: ``param_rw`` (default) / ``param_var`` / ``param_pca``; engines ``analytic`` /
``montecarlo`` (default). Catalogued-but-unbuilt names raise ``NotImplementedError``.
"""
from __future__ import annotations

from enum import StrEnum

from alphavar.options.lib.forecast.smile._engine import SmileAnalyticEngine, SmileMonteCarloEngine
from alphavar.options.lib.forecast.smile.param_pca import ParamPCA
from alphavar.options.lib.forecast.smile.param_rw import ParamRandomWalk
from alphavar.options.lib.forecast.smile.param_var import ParamVAR1


class MaturityConvention(StrEnum):
    """How the historical θ slices relate to the forecast tenor."""

    FIXED_EXPIRATION = "fixed_expiration"  # model one expiration's θ (mixes tenors as it rolls down)
    CONSTANT_MATURITY = "constant_maturity"  # interpolate to the fixed target tenor first (correct)


_MODELS = {m.name: m for m in (ParamRandomWalk, ParamVAR1, ParamPCA)}
_PLANNED_ENGINES = frozenset({"bootstrap"})

DEFAULT_SMILE_FORECAST_MODEL = ParamRandomWalk.name
DEFAULT_SMILE_FORECAST_ENGINE = SmileMonteCarloEngine.name


def make_smile_forecast_model(name: str = DEFAULT_SMILE_FORECAST_MODEL, *, n_components: int = 3):
    """Smile θ-model instance by name (``param_rw`` / ``param_var`` / ``param_pca``)."""
    if name not in _MODELS:
        raise ValueError(f"unknown smile forecast model {name!r}; available: {sorted(_MODELS)}")
    if name == ParamPCA.name:
        return ParamPCA(n_components=n_components)
    return _MODELS[name]()


def make_smile_engine(name: str = DEFAULT_SMILE_FORECAST_ENGINE, *, n: int = 10000, seed: int | None = None):
    """Smile engine by name (``montecarlo`` default; ``analytic``); planned names raise."""
    if name in _PLANNED_ENGINES:
        raise NotImplementedError(f"engine {name!r} is planned (T27), not yet implemented")
    if name == SmileMonteCarloEngine.name:
        return SmileMonteCarloEngine(n=n, seed=seed)
    if name == SmileAnalyticEngine.name:
        return SmileAnalyticEngine()
    raise ValueError(f"unknown smile engine {name!r}; use 'analytic' or 'montecarlo'")


def resolve_maturity(maturity: MaturityConvention | str) -> MaturityConvention:
    """Validate the maturity convention (both ``fixed_expiration`` and ``constant_maturity`` built)."""
    return MaturityConvention(maturity)
