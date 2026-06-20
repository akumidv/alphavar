"""Black-76 (forward) option pricing + implied volatility — pure functions (R3, T21).

Deribit (and most listed crypto options) quote on the **forward**: the option's underlying
is a future, so ``underlying_price`` is the forward ``F`` and the discounted-forward
(Black-76) model is the right one — no separate carry/dividend term. With the default
``rate=0`` it reduces to the undiscounted forward model used on Deribit.

DataFrame in / scalars or arrays in → arrays out; no I/O, no state (the facade
``OptionsPricer`` wires these to columns). Vectorized over numpy arrays.

# 4VERIFY (owner, D2): the Black-76 formulas, the degenerate (T<=0 / vol<=0)
# intrinsic fallback, and the bisection implied-vol solver. Pinned by reference values +
# round-trip tests in tests/unit/options/lib/pricer/black_scholes_test.py.
"""
from __future__ import annotations

from math import erf, sqrt

import numpy as np

_SQRT2 = sqrt(2.0)
_norm_cdf_vec = np.vectorize(erf, otypes=[float])


def norm_cdf(x: np.ndarray | float) -> np.ndarray:
    """Standard normal CDF Φ(x) = ½(1 + erf(x/√2)) — exact, vectorized via ``math.erf``."""
    return 0.5 * (1.0 + _norm_cdf_vec(np.asarray(x, dtype=float) / _SQRT2))


def _d1_d2(forward, strike, t_years, sigma):
    f = np.asarray(forward, dtype=float)
    k = np.asarray(strike, dtype=float)
    t = np.asarray(t_years, dtype=float)
    s = np.asarray(sigma, dtype=float)
    total_vol = s * np.sqrt(np.maximum(t, 0.0))  # σ√T
    with np.errstate(divide="ignore", invalid="ignore"):
        d1 = (np.log(f / k) + 0.5 * s * s * t) / total_vol
        d2 = d1 - total_vol
    return d1, d2, f, k, t, total_vol


def bs_forward_price(forward, strike, t_years, sigma, is_call, rate: float = 0.0) -> np.ndarray:
    """Black-76 option price on a forward ``F``.

    call = e^{-rT}[F·Φ(d1) − K·Φ(d2)];  put = e^{-rT}[K·Φ(−d2) − F·Φ(−d1)],
    d1 = [ln(F/K) + ½σ²T] / (σ√T),  d2 = d1 − σ√T.
    Degenerate inputs (T≤0 or σ≤0, i.e. σ√T==0) → discounted intrinsic value.
    """
    d1, d2, f, k, t, total_vol = _d1_d2(forward, strike, t_years, sigma)
    is_call = np.asarray(is_call, dtype=bool)
    disc = np.exp(-rate * t)
    call = disc * (f * norm_cdf(d1) - k * norm_cdf(d2))
    put = disc * (k * norm_cdf(-d2) - f * norm_cdf(-d1))
    priced = np.where(is_call, call, put)
    intrinsic = disc * np.where(is_call, np.maximum(f - k, 0.0), np.maximum(k - f, 0.0))
    return np.where(total_vol > 0.0, priced, intrinsic)


def bs_vega(forward, strike, t_years, sigma, rate: float = 0.0) -> np.ndarray:
    """∂price/∂σ (per 1.00 of vol, not per 1%). Same for calls and puts."""
    d1, _, f, _, t, total_vol = _d1_d2(forward, strike, t_years, sigma)
    phi = np.exp(-0.5 * d1 * d1) / sqrt(2.0 * np.pi)  # standard normal pdf
    vega = np.exp(-rate * t) * f * phi * np.sqrt(np.maximum(t, 0.0))
    return np.where(total_vol > 0.0, vega, 0.0)


def implied_vol(
    price, forward, strike, t_years, is_call, rate: float = 0.0,
    lo: float = 1e-6, hi: float = 5.0, iters: int = 100,
) -> np.ndarray:
    """Implied volatility by **bisection** on σ in [lo, hi] (robust, derivative-free).

    Vectorized: returns NaN where the price is outside the model's no-arbitrage bracket
    [intrinsic, forward-bound] (no σ reproduces it). ``iters=100`` bisections over a 5.0-wide
    bracket give ~5·5/2^100 precision — far below quote resolution.
    """
    target = np.asarray(price, dtype=float)
    shape = np.broadcast(target, np.asarray(forward), np.asarray(strike), np.asarray(t_years)).shape
    lo_arr = np.full(shape, lo, dtype=float)
    hi_arr = np.full(shape, hi, dtype=float)
    p_lo = bs_forward_price(forward, strike, t_years, lo_arr, is_call, rate)
    p_hi = bs_forward_price(forward, strike, t_years, hi_arr, is_call, rate)
    # solvable only if the target lies within [p(lo), p(hi)] (monotonic increasing in σ)
    solvable = (target >= p_lo) & (target <= p_hi)
    for _ in range(iters):
        mid = 0.5 * (lo_arr + hi_arr)
        p_mid = bs_forward_price(forward, strike, t_years, mid, is_call, rate)
        too_low = p_mid < target
        lo_arr = np.where(too_low, mid, lo_arr)
        hi_arr = np.where(too_low, hi_arr, mid)
    sigma = 0.5 * (lo_arr + hi_arr)
    return np.where(solvable, sigma, np.nan)
