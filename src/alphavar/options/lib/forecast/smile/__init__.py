"""Smile-target forecast (T27 iteration 3, R5): forecast the SVI parameter vector θ.

Forecast one expiration's smile by modelling its calibrated SVI θ = (a, b, ρ, m, σ) over history
(``param_rw`` / ``param_var`` / ``param_pca``) and decoding the terminal θ back to a smile at the
target tenor. A sibling factory of the scalar forecast and of ``pricer.smile.make_smile_model``
(ADR 0002), because the state is a parameter vector and the result is a ``SmileForecast``.
"""
from alphavar.options.lib.forecast.smile._base import (
    SMILE_PARAM_NAMES,
    SmileForecast,
    SmileForecastModel,
    ThetaProcess,
)
from alphavar.options.lib.forecast.smile._decode import decode_smile, sample_mvn
from alphavar.options.lib.forecast.smile._factory import (
    DEFAULT_SMILE_FORECAST_ENGINE,
    DEFAULT_SMILE_FORECAST_MODEL,
    MaturityConvention,
    make_smile_engine,
    make_smile_forecast_model,
    resolve_maturity,
)
from alphavar.options.lib.forecast.smile._theta import build_theta_history, default_expiration
from alphavar.options.lib.forecast.smile.param_pca import ParamPCA
from alphavar.options.lib.forecast.smile.param_rw import ParamRandomWalk
from alphavar.options.lib.forecast.smile.param_var import ParamVAR1

__all__ = [
    "SMILE_PARAM_NAMES",
    "SmileForecast",
    "SmileForecastModel",
    "ThetaProcess",
    "decode_smile",
    "sample_mvn",
    "MaturityConvention",
    "make_smile_forecast_model",
    "make_smile_engine",
    "resolve_maturity",
    "DEFAULT_SMILE_FORECAST_MODEL",
    "DEFAULT_SMILE_FORECAST_ENGINE",
    "build_theta_history",
    "default_expiration",
    "ParamRandomWalk",
    "ParamVAR1",
    "ParamPCA",
]
