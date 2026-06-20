"""Volatility-smile parametrizations + arbitrage-free fitting (T21, R5).

``make_smile_model(name)`` returns a smile model (default SVI); each model's ``fit`` returns a
``SmileResult`` that predicts ``iv(k)`` over log-moneyness and exposes a numeric butterfly
no-arbitrage check. The DataFrame-level driver lives in ``pricer._smile_enrich``.
"""
from alphavar.options.lib.pricer.smile._base import SmileModel, SmileResult
from alphavar.options.lib.pricer.smile._factory import DEFAULT_SMILE_MODEL, SMILE_MODELS, make_smile_model
from alphavar.options.lib.pricer.smile.quadratic import QuadraticSmile
from alphavar.options.lib.pricer.smile.sabr import SABRSmile
from alphavar.options.lib.pricer.smile.svi import SVISmile

__all__ = [
    "SmileModel",
    "SmileResult",
    "make_smile_model",
    "SMILE_MODELS",
    "DEFAULT_SMILE_MODEL",
    "SVISmile",
    "QuadraticSmile",
    "SABRSmile",
]
