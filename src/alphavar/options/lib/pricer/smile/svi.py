"""Raw SVI smile (Gatheral): total variance w(k) = a + b·(ρ·(k−m) + √((k−m)² + σ²)) (T21).

The industry-standard arbitrage-friendly slice parametrization. Calibrated quasi-explicitly
(Zeliade): for a fixed pair ``(m, σ)`` the remaining ``(a, b, ρ)`` solve a *linear* least
squares in ``w``; the outer 2-D search over ``(m, σ)`` is the pure-numpy Nelder–Mead. Returned
parameters satisfy the basic domain constraints (b ≥ 0, |ρ| < 1, σ > 0, w ≥ 0); full butterfly
no-arb is verified by ``SmileResult.is_butterfly_free``.

# 4VERIFY (owner, D2): the SVI form, the quasi-explicit inner solve + clipping, and the
# total-variance (w = iv²·T) working space. Pinned by reference + round-trip tests.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.pricer.smile._base import SmileModel, SmileResult
from alphavar.options.lib.pricer.smile._optimize import minimize_nelder_mead

_RHO_CAP = 0.999


def _raw_w(k: np.ndarray, a: float, b: float, rho: float, m: float, sigma: float) -> np.ndarray:
    x = k - m
    return a + b * (rho * x + np.sqrt(x * x + sigma * sigma))


def _inner_solve(k, w_obs, sw, m, sigma) -> tuple[float, float, float]:
    """Best (a, b, ρ) for fixed (m, σ) by linear LS on w = a + (bρ)·x + b·z, then clip to domain."""
    x = k - m
    z = np.sqrt(x * x + sigma * sigma)
    basis = np.vstack([np.ones_like(k), x, z]).T
    coef, *_ = np.linalg.lstsq(basis * sw[:, None], w_obs * sw, rcond=None)
    a, p, q = (float(c) for c in coef)
    b = max(q, 0.0)
    rho = float(np.clip(p / b, -_RHO_CAP, _RHO_CAP)) if b > 0.0 else 0.0
    # keep total variance non-negative: min over k of w is a + b·σ·√(1−ρ²)
    a = max(a, -b * sigma * np.sqrt(max(1.0 - rho * rho, 0.0)))
    return a, b, rho


class SVISmile(SmileModel):
    """Raw-SVI total-variance smile, quasi-explicit calibration."""

    name = "svi"

    def fit(self, k: np.ndarray, iv: np.ndarray, t_years: float, weights: np.ndarray | None = None) -> SmileResult:
        k, iv, weight = self._clean(k, iv, weights)
        t = max(float(t_years), 1e-12)
        if k.size < 5:  # SVI needs ~5 points; fall back to a flat slice at the mean vol
            level = float(np.average(iv, weights=weight)) if k.size else float("nan")
            params = {"a": level * level * t, "b": 0.0, "rho": 0.0, "m": 0.0, "sigma": 0.1}
            return SmileResult(self, params, t, lambda kk: np.full_like(kk, level))

        w_obs = iv * iv * t  # work in total variance
        sw = np.sqrt(weight)

        def objective(ms: np.ndarray) -> float:
            m, log_sigma = ms
            sigma = float(np.exp(log_sigma))  # σ > 0 by construction
            a, b, rho = _inner_solve(k, w_obs, sw, m, sigma)
            resid = (_raw_w(k, a, b, rho, m, sigma) - w_obs) * sw
            return float(resid @ resid)

        m0 = float(k[np.argmin(iv)])  # start at the lowest-vol strike
        best_ms, _ = minimize_nelder_mead(objective, np.array([m0, np.log(0.1)]), step=0.2)
        m, sigma = float(best_ms[0]), float(np.exp(best_ms[1]))
        a, b, rho = _inner_solve(k, w_obs, sw, m, sigma)
        params = {"a": a, "b": b, "rho": rho, "m": m, "sigma": sigma}

        def predict(kk: np.ndarray) -> np.ndarray:
            return np.sqrt(np.maximum(_raw_w(kk, a, b, rho, m, sigma), 0.0) / t)

        return SmileResult(self, params, t, predict)
