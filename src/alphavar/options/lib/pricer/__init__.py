"""Pure option-pricing logic (Black-76 forward model + smile fitting) — T21 / R3/R5."""

from alphavar.options.lib.pricer._enrich import add_fair_price, add_model_iv, years_to_expiry
from alphavar.options.lib.pricer._smile_enrich import add_smile_iv, fit_smile_slices
from alphavar.options.lib.pricer.black_scholes import (
    bs_forward_price,
    bs_vega,
    implied_vol,
    norm_cdf,
)
from alphavar.options.lib.pricer.smile import DEFAULT_SMILE_MODEL, SmileModel, SmileResult, make_smile_model

__all__ = [
    "bs_forward_price",
    "bs_vega",
    "implied_vol",
    "norm_cdf",
    "add_model_iv",
    "add_fair_price",
    "years_to_expiry",
    "add_smile_iv",
    "fit_smile_slices",
    "make_smile_model",
    "SmileModel",
    "SmileResult",
    "DEFAULT_SMILE_MODEL",
]
