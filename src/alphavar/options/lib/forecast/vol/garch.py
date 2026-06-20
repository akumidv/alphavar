"""GARCH(1,1) volatility forecast — variance term structure (analytic) + realized-vol MC (T27).

Reuses the shared estimator (``forecast._garch.estimate_garch``). The multi-step variance term
structure ``E[σ²_{t+k}] = σ²_unc + (α+β)^{k-1}·(σ²_{t+1} − σ²_unc)`` gives the **expected** average
variance over the horizon (analytic point); Monte-Carlo simulation of the same recursion gives the
**distribution** of realized vol across paths (so ``garch`` supports both engines, unlike the
flat-term-structure point models).

# 4VERIFY (owner, D2): the variance term structure formula, the horizon-average expected variance
# → annualized vol (analytic), and the MC realized-vol = √(mean ε²_k / dt) over n_steps = round(H/dt).
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import FittedProcess, ForecastModel, ForecastTarget
from alphavar.options.lib.forecast._garch import GarchParams, estimate_garch
from alphavar.options.lib.forecast._stats import DegenerateTerminal


class _GarchVol(FittedProcess):
    """Calibrated GARCH(1,1) vol process: analytic expected vol + MC realized-vol distribution."""

    def __init__(self, ref_vol: float, horizon_years: float, params: GarchParams, dt_years: float, n_steps: int):
        self.target = ForecastTarget.VOL
        self.model_name = "garch"
        self.spot = float(ref_vol)
        self.horizon_years = float(horizon_years)
        self.params = params
        self.dt_years = float(dt_years)
        self.n_steps = int(n_steps)

    def _expected_step_var(self) -> float:
        """Horizon-average expected per-step variance from the GARCH term structure."""
        k = np.arange(1, self.n_steps + 1)
        term = self.params.uncond_var + self.params.persistence ** (k - 1) * (
            self.params.sigma2_next - self.params.uncond_var
        )
        return float(np.mean(term))

    def analytic_terminal(self) -> DegenerateTerminal:
        return DegenerateTerminal(np.sqrt(max(self._expected_step_var(), 0.0) / self.dt_years))

    def sample_terminal(self, n: int, rng: np.random.Generator) -> np.ndarray:
        n = int(n)
        sigma2 = np.full(n, self.params.sigma2_next, dtype=float)
        sum_sq = np.zeros(n, dtype=float)
        for _ in range(self.n_steps):
            eps = np.sqrt(sigma2) * rng.standard_normal(n)
            sum_sq += eps * eps
            sigma2 = self.params.omega + self.params.alpha * eps * eps + self.params.beta * sigma2
        return np.sqrt((sum_sq / self.n_steps) / self.dt_years)


class GarchVol(ForecastModel):
    """GARCH(1,1) volatility: analytic variance term structure + Monte-Carlo realized vol."""

    name = "garch"
    target = ForecastTarget.VOL
    supports = frozenset({"analytic", "montecarlo"})

    def fit(self, prices: np.ndarray, dt_years: float, horizon_years: float) -> _GarchVol:
        returns, _ = self._log_returns(prices)
        params = estimate_garch(returns)
        n_steps = max(1, int(round(horizon_years / dt_years)))
        ref = float(np.sqrt(self._step_var(returns) / dt_years))
        return _GarchVol(ref, horizon_years, params, dt_years, n_steps)
