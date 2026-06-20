"""Driftless multivariate random walk on the SVI parameter vector θ (T27 iteration 3).

θ_{t+1} = θ_t + ε,  ε ~ N(0, Σ_step),  Σ_step = sample covariance of the historical θ increments.
The terminal θ over ``n_steps`` is then Gaussian, centred at the last observed θ (driftless) with
covariance ``n_steps · Σ_step`` (i.i.d. increments).

# 4VERIFY (owner, D2): driftless mean = last θ, terminal covariance = n_steps · cov(Δθ).
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast.smile._base import SMILE_PARAM_NAMES, SmileForecastModel, ThetaProcess


def increment_cov(theta: np.ndarray) -> np.ndarray:
    """Sample covariance of the one-step θ increments Δθ (``(p, p)``, zero if a single increment)."""
    diffs = np.diff(theta, axis=0)
    if diffs.shape[0] < 2:
        return np.zeros((theta.shape[1], theta.shape[1]), dtype=float)
    return np.atleast_2d(np.cov(diffs, rowvar=False, ddof=1))


class ParamRandomWalk(SmileForecastModel):
    """Driftless multivariate random walk on θ — the smile-forecast baseline."""

    name = "param_rw"
    supports = frozenset({"analytic", "montecarlo"})

    def fit(self, theta_history: np.ndarray, dt_years: float, horizon_years: float, t_target: float) -> ThetaProcess:
        theta, _ = self._prepare(theta_history)
        n_steps = self._n_steps(horizon_years, dt_years)
        theta0 = theta[-1]
        cov = n_steps * increment_cov(theta)
        return ThetaProcess(self.name, SMILE_PARAM_NAMES, t_target, horizon_years, theta0, theta0.copy(), cov)
