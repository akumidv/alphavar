"""SABR smile via Hagan's lognormal implied-vol expansion, β = 1 (T21).

β = 1 (lognormal) is the natural choice on a forward (Black-76 world): the forward F then
cancels and the smile depends only on log-moneyness ``k = ln(K/F)``, vol-of-vol ``ν``,
correlation ``ρ`` and level ``α``. Calibrated by pure-numpy Nelder–Mead over
``(log α, atanh ρ, log ν)`` (so α, ν > 0 and |ρ| < 1 by construction). Not arbitrage-free by
construction — checked post-fit via ``SmileResult.is_butterfly_free``.

# 4VERIFY (owner, D2): the β=1 Hagan formula, the ATM (z→0) limit, and the calibration
# parametrization. Pinned by reference + round-trip tests.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.pricer.smile._base import SmileModel, SmileResult
from alphavar.options.lib.pricer.smile._optimize import minimize_nelder_mead


def _sabr_iv_beta1(k: np.ndarray, alpha: float, rho: float, nu: float, t: float) -> np.ndarray:
    """Hagan β=1 lognormal implied vol at log-moneyness ``k = ln(K/F)``."""
    if alpha <= 0.0 or nu <= 0.0:
        return np.full_like(np.asarray(k, dtype=float), np.nan)
    ln_fk = -np.asarray(k, dtype=float)  # ln(F/K)
    z = (nu / alpha) * ln_fk
    sqrt_term = np.sqrt(1.0 - 2.0 * rho * z + z * z)
    chi = np.log((sqrt_term + z - rho) / (1.0 - rho))
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(np.abs(z) < 1e-8, 1.0, z / chi)  # z/χ(z) → 1 as z → 0 (ATM)
    factor = 1.0 + (0.25 * rho * nu * alpha + (2.0 - 3.0 * rho * rho) / 24.0 * nu * nu) * t
    return alpha * ratio * factor


class SABRSmile(SmileModel):
    """SABR (β = 1) lognormal smile, Hagan approximation."""

    name = "sabr"
    beta = 1.0

    def fit(self, k: np.ndarray, iv: np.ndarray, t_years: float, weights: np.ndarray | None = None) -> SmileResult:
        k, iv, weight = self._clean(k, iv, weights)
        t = max(float(t_years), 1e-12)
        if k.size < 3:  # too few points for 3 params → flat slice at the mean vol
            level = float(np.average(iv, weights=weight)) if k.size else float("nan")
            params = {"alpha": level, "rho": 0.0, "nu": 0.0, "beta": self.beta}
            return SmileResult(self, params, t, lambda kk: np.full_like(kk, level))

        sw = np.sqrt(weight)
        alpha0 = float(iv[np.argmin(np.abs(k))])  # ATM-ish vol

        def objective(p: np.ndarray) -> float:
            alpha, rho, nu = np.exp(p[0]), np.tanh(p[1]), np.exp(p[2])
            resid = (_sabr_iv_beta1(k, alpha, rho, nu, t) - iv) * sw
            return float(np.nan_to_num(resid @ resid, nan=1e6))

        p0 = np.array([np.log(max(alpha0, 1e-3)), 0.0, np.log(0.5)])
        best, _ = minimize_nelder_mead(objective, p0, step=0.3)
        alpha, rho, nu = float(np.exp(best[0])), float(np.tanh(best[1])), float(np.exp(best[2]))
        params = {"alpha": alpha, "rho": rho, "nu": nu, "beta": self.beta}

        def predict(kk: np.ndarray) -> np.ndarray:
            return _sabr_iv_beta1(kk, alpha, rho, nu, t)

        return SmileResult(self, params, t, predict)
