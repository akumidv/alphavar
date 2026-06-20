"""Surface-forecast factory — pick a stacked-θ model / engine by name (T27 iteration 4).

The surface state is a *stack* of SVI θ across constant-maturity tenor nodes, so the dynamics reuse
the verified smile θ-models on the longer vector (ADR 0002 — the same Process × Engine axes):
- ``svi_surface`` — node-wise random walk on the stacked θ (driftless; flat ``w/τ`` T-extrapolation
  beyond the node range is in the decode). Default.
- ``svi_surface_var`` — mean-reverting VAR(1) on the stacked θ.
- ``pca_factor`` — PCA-reduced random walk: the dominant joint surface-movement modes.

Engines ``analytic`` / ``montecarlo`` (default) build a ``SurfaceForecast``.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast.smile.param_pca import ParamPCA
from alphavar.options.lib.forecast.smile.param_rw import ParamRandomWalk
from alphavar.options.lib.forecast.smile.param_var import ParamVAR1
from alphavar.options.lib.forecast.surface._engine import SurfaceAnalyticEngine, SurfaceMonteCarloEngine

# surface model name → the stacked-θ dynamics it maps to
_MODELS = {
    "svi_surface": ParamRandomWalk,
    "svi_surface_var": ParamVAR1,
    "pca_factor": ParamPCA,
}
_PLANNED_ENGINES = frozenset({"bootstrap"})

DEFAULT_SURFACE_FORECAST_MODEL = "svi_surface"
DEFAULT_SURFACE_FORECAST_ENGINE = "montecarlo"


def make_surface_forecast_model(name: str = DEFAULT_SURFACE_FORECAST_MODEL, *, n_components: int = 5):
    """Surface θ-model by name (``svi_surface`` / ``svi_surface_var`` / ``pca_factor``)."""
    if name not in _MODELS:
        raise ValueError(f"unknown surface forecast model {name!r}; available: {sorted(_MODELS)}")
    if name == "pca_factor":
        return ParamPCA(n_components=n_components)
    return _MODELS[name]()


def make_surface_engine(
    name: str, tenor_nodes: np.ndarray, *, n: int = 10000, seed: int | None = None
):
    """Surface engine by name (``montecarlo`` default; ``analytic``); planned names raise."""
    if name in _PLANNED_ENGINES:
        raise NotImplementedError(f"engine {name!r} is planned (T27), not yet implemented")
    if name == SurfaceMonteCarloEngine.name:
        return SurfaceMonteCarloEngine(tenor_nodes, n=n, seed=seed)
    if name == SurfaceAnalyticEngine.name:
        return SurfaceAnalyticEngine(tenor_nodes)
    raise ValueError(f"unknown surface engine {name!r}; use 'analytic' or 'montecarlo'")
