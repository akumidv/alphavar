"""GARCH(1,1) price model — conditional-vol dynamics, Monte-Carlo terminal (T27).

The terminal price is **not** log-normal (returns have time-varying variance), so there is no
analytic distribution — the engine must be ``montecarlo``: it simulates ``round(H/dt)`` one-step
recursions forward from the last conditional variance. The GARCH(1,1) estimator is shared with the
vol target (``forecast._garch.estimate_garch``).

# 4VERIFY (owner, D2): the forward simulation (σ²_next seed, n_steps = round(H/dt) discretization,
# ε_k = σ_k·z_k, log-price accumulation). The estimator math lives in ``forecast._garch``.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import FittedProcess, ForecastModel, ForecastTarget
from alphavar.options.lib.forecast._garch import estimate_garch


class _GarchFitted(FittedProcess):
    """Calibrated GARCH(1,1) price process; MC-only (no closed-form terminal price)."""

    def __init__(
        self,
        spot: float,
        horizon_years: float,
        mu: float,
        omega: float,
        alpha: float,
        beta: float,
        sigma2_next: float,
        n_steps: int,
    ):
        self.target = ForecastTarget.PRICE
        self.model_name = "garch"
        self.spot = float(spot)
        self.horizon_years = float(horizon_years)
        self.mu = mu
        self.omega = omega
        self.alpha = alpha
        self.beta = beta
        self.sigma2_next = sigma2_next
        self.n_steps = n_steps

    def sample_terminal(self, n: int, rng: np.random.Generator) -> np.ndarray:
        n = int(n)
        sigma2 = np.full(n, self.sigma2_next, dtype=float)
        log_sum = np.zeros(n, dtype=float)
        for _ in range(self.n_steps):
            eps = np.sqrt(sigma2) * rng.standard_normal(n)
            log_sum += self.mu + eps
            sigma2 = self.omega + self.alpha * eps * eps + self.beta * sigma2
        return self.spot * np.exp(log_sum)


class GarchPrice(ForecastModel):
    """GARCH(1,1) Gaussian-MLE conditional-vol price model; Monte-Carlo only."""

    name = "garch"
    target = ForecastTarget.PRICE
    supports = frozenset({"montecarlo"})

    def fit(self, prices: np.ndarray, dt_years: float, horizon_years: float) -> _GarchFitted:
        returns, spot = self._log_returns(prices)
        p = estimate_garch(returns)
        n_steps = max(1, int(round(horizon_years / dt_years)))
        return _GarchFitted(spot, horizon_years, p.mu, p.omega, p.alpha, p.beta, p.sigma2_next, n_steps)
