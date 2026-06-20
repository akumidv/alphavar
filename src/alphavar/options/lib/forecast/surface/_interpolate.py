"""Cross-expiration tenor interpolation in total variance (T27 iteration 4, R5).

A surface is a smile per expiration; to read it at an arbitrary tenor τ (e.g. a constant-maturity
node, or a forecast horizon) we interpolate **total implied variance** ``w = σ²·τ`` — the
calendar-no-arbitrage–friendly space (``w`` should be non-decreasing in τ at fixed k). Between two
bracketing expirations ``w`` is linear in τ; outside the observed range we hold the **variance rate**
``w/τ`` of the nearest expiration (flat-forward-variance extrapolation = the catalog's
"T-extrapolation"). This is the cross-expiration piece that both the surface forecast and the
``constant_maturity`` smile-forecast maturity convention (B) build on.

# 4VERIFY (owner, D2): linear-in-w interpolation in τ, flat ``w/τ`` extrapolation beyond the range,
# and σ(k,τ) = √(w(k,τ)/τ).
"""
from __future__ import annotations

import numpy as np


def interp_total_variance(tenors: np.ndarray, total_vars: np.ndarray, tau: float) -> np.ndarray:
    """Total variance at tenor ``tau`` from per-tenor curves.

    ``tenors`` — ascending tenors ``(m,)``; ``total_vars`` — ``w`` per tenor ``(m, K)`` (one row per
    tenor, columns = a shared log-moneyness grid); returns ``w(·, tau)`` ``(K,)``.
    """
    tenors = np.asarray(tenors, dtype=float)
    w = np.atleast_2d(np.asarray(total_vars, dtype=float))
    tau = float(tau)
    if tenors.size == 1:  # single expiration → flat variance rate
        return w[0] * (tau / tenors[0])
    if tau <= tenors[0]:
        return w[0] * (tau / tenors[0])
    if tau >= tenors[-1]:
        return w[-1] * (tau / tenors[-1])
    hi = int(np.searchsorted(tenors, tau))
    lo = hi - 1
    frac = (tau - tenors[lo]) / (tenors[hi] - tenors[lo])
    return w[lo] + frac * (w[hi] - w[lo])


def constant_maturity_iv(smiles_by_tenor: dict[float, object], k: np.ndarray, tau: float) -> np.ndarray:
    """σ(k, τ) from ``{tenor: SmileResult}`` via total-variance interpolation in τ."""
    k = np.atleast_1d(np.asarray(k, dtype=float))
    tenors = np.array(sorted(smiles_by_tenor), dtype=float)
    w = np.vstack([smiles_by_tenor[t].total_variance(k) for t in tenors])
    w_tau = interp_total_variance(tenors, w, tau)
    return np.sqrt(np.maximum(w_tau, 0.0) / max(tau, 1e-12))
