"""Mean-reverting VAR(1) on the SVI parameter vector θ (T27 iteration 3).

θ_t = c + θ_{t-1} · A + ε,  ε ~ N(0, Σ_ε)  (row-vector convention), with ``(c, A)`` from a
multivariate OLS of θ_t on θ_{t-1} and Σ_ε the residual covariance. The deterministic mean is
iterated ``n_steps`` forward from the last θ; the terminal covariance accumulates along the same
recursion (``V_k = Aᵀ V_{k-1} A + Σ_ε``). A stable A (eigenvalues < 1) makes the forecast revert
toward the process mean ``c·(I − A)⁻¹`` — unlike the driftless random walk.

Falls back to a driftless random walk when the history is too short to identify ``(c, A)``
(needs more rows than the ``p + 1`` regression coefficients).

# 4VERIFY (owner, D2): the OLS ``(c, A)`` orientation (θ_t = c + θ_{t-1}·A), the forward mean
# iteration, and the covariance recursion ``V_k = Aᵀ V_{k-1} A + Σ_ε``.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast.smile._base import SMILE_PARAM_NAMES, SmileForecastModel, ThetaProcess
from alphavar.options.lib.forecast.smile.param_rw import increment_cov


class ParamVAR1(SmileForecastModel):
    """First-order vector autoregression on θ (mean-reverting when A is stable)."""

    name = "param_var"
    supports = frozenset({"analytic", "montecarlo"})

    def fit(self, theta_history: np.ndarray, dt_years: float, horizon_years: float, t_target: float) -> ThetaProcess:
        theta, p = self._prepare(theta_history)
        n_steps = self._n_steps(horizon_years, dt_years)
        theta0 = theta[-1]

        if theta.shape[0] <= p + 1:  # under-identified VAR → driftless RW
            cov = n_steps * increment_cov(theta)
            return ThetaProcess(self.name, SMILE_PARAM_NAMES, t_target, horizon_years, theta0, theta0.copy(), cov)

        x_prev = theta[:-1]
        y_next = theta[1:]
        design = np.hstack([np.ones((x_prev.shape[0], 1)), x_prev])  # [1, θ_{t-1}]
        coef, *_ = np.linalg.lstsq(design, y_next, rcond=None)  # (p+1, p): row0 = c, rest = A
        c = coef[0]
        a_mat = coef[1:]
        resid = y_next - design @ coef
        sigma_eps = np.atleast_2d(np.cov(resid, rowvar=False, ddof=1)) if resid.shape[0] > 1 else np.zeros((p, p))

        mean = theta0.copy()
        cov = np.zeros((p, p), dtype=float)
        for _ in range(n_steps):
            mean = c + mean @ a_mat
            cov = a_mat.T @ cov @ a_mat + sigma_eps
        return ThetaProcess(self.name, SMILE_PARAM_NAMES, t_target, horizon_years, theta0, mean, cov)
