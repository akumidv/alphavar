"""Surface-target forecast (T27 iteration 4, R5): forecast the whole vol surface.

The surface state is a stack of SVI θ at constant-maturity tenor nodes (cross-expiration
total-variance interpolation, ``_interpolate`` / ``_nodes``); the dynamics reuse the verified smile
θ-models on the longer vector (``svi_surface`` RW / ``svi_surface_var`` VAR / ``pca_factor`` PCA), and
the terminal stacked θ decodes back to a ``SurfaceForecast`` (expected surface + scenario σ(k,τ)
bands, butterfly + calendar no-arb). The constant-maturity interpolation here also powers the
``constant_maturity`` smile-forecast maturity convention (B).
"""
from alphavar.options.lib.forecast.surface._base import (
    SurfaceForecast,
    SurfaceResult,
    decode_surface,
)
from alphavar.options.lib.forecast.surface._factory import (
    DEFAULT_SURFACE_FORECAST_ENGINE,
    DEFAULT_SURFACE_FORECAST_MODEL,
    make_surface_engine,
    make_surface_forecast_model,
)
from alphavar.options.lib.forecast.surface._interpolate import constant_maturity_iv, interp_total_variance
from alphavar.options.lib.forecast.surface._nodes import DEFAULT_TENOR_NODES, constant_maturity_theta_history

__all__ = [
    "SurfaceForecast",
    "SurfaceResult",
    "decode_surface",
    "make_surface_forecast_model",
    "make_surface_engine",
    "DEFAULT_SURFACE_FORECAST_MODEL",
    "DEFAULT_SURFACE_FORECAST_ENGINE",
    "constant_maturity_iv",
    "interp_total_variance",
    "constant_maturity_theta_history",
    "DEFAULT_TENOR_NODES",
]
