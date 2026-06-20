"""Pure option-pricing logic (Black-76 forward model) — T21 / R3."""

from alphavar.options.lib.pricer._enrich import add_fair_price, add_model_iv, years_to_expiry
from alphavar.options.lib.pricer.black_scholes import (
    bs_forward_price,
    bs_vega,
    implied_vol,
    norm_cdf,
)

__all__ = [
    "bs_forward_price",
    "bs_vega",
    "implied_vol",
    "norm_cdf",
    "add_model_iv",
    "add_fair_price",
    "years_to_expiry",
]
