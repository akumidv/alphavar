"""Model-free empirical (historical-return) price model (T27 it.5).

No parametric law: the horizon return is the **sum of ``n`` resampled historical log-returns**
(``n = round(H/dt)``), and the terminal price is ``S₀·exp(Σ resampled r)``. The empirical return
distribution carries its own drift, fat tails and skew, so this is the honest "history repeats the
returns" baseline. No closed form ⇒ no ``analytic`` engine.

Two resampling modes (the engine axis):
- ``montecarlo`` → ``sample_terminal``: **i.i.d.** resample (each step drawn independently).
- ``bootstrap`` → ``bootstrap_terminal``: **moving-block** bootstrap — contiguous blocks (wrap-around)
  preserve short-range autocorrelation/volatility clustering; block length defaults to ``round(n^{1/3})``.

# 4VERIFY (owner, D2): horizon return = Σ of n=round(H/dt) resampled log-returns, S_T=S₀·exp(Σr);
# i.i.d. vs moving-block (wrap-around) resampling and the n^{1/3} default block length.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import FittedProcess, ForecastModel, ForecastTarget


class _EmpiricalFitted(FittedProcess):
    """Historical log-returns resampled over ``n_steps`` to a terminal price; MC + bootstrap."""

    def __init__(self, spot: float, horizon_years: float, returns: np.ndarray, n_steps: int):
        self.target = ForecastTarget.PRICE
        self.model_name = "empirical"
        self.spot = float(spot)
        self.horizon_years = float(horizon_years)
        self.returns = np.asarray(returns, dtype=float)
        self.n_steps = int(n_steps)

    def sample_terminal(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """i.i.d. bootstrap: ``n`` paths, each a sum of ``n_steps`` independently-drawn returns."""
        idx = rng.integers(0, self.returns.size, size=(int(n), self.n_steps))
        return self.spot * np.exp(self.returns[idx].sum(axis=1))

    def bootstrap_terminal(self, n: int, rng: np.random.Generator, block: int | None = None) -> np.ndarray:
        """Moving-block bootstrap: concatenate contiguous wrap-around blocks to preserve dependence."""
        r = self.returns
        ln = max(1, int(round(self.n_steps ** (1.0 / 3.0))) if block is None else int(block))
        n_blocks = int(np.ceil(self.n_steps / ln))
        starts = rng.integers(0, r.size, size=(int(n), n_blocks))  # one start per block, per path
        # each block = ln contiguous returns (mod r.size); stitch blocks, keep the first n_steps
        idx = (starts[:, :, None] + np.arange(ln)) % r.size  # (n, n_blocks, ln)
        idx = idx.reshape(int(n), n_blocks * ln)[:, : self.n_steps]
        return self.spot * np.exp(r[idx].sum(axis=1))


class EmpiricalPrice(ForecastModel):
    """Empirical historical-return price model; resampled terminal (montecarlo / bootstrap)."""

    name = "empirical"
    target = ForecastTarget.PRICE
    supports = frozenset({"montecarlo", "bootstrap"})

    def fit(self, prices: np.ndarray, dt_years: float, horizon_years: float) -> _EmpiricalFitted:
        returns, spot = self._log_returns(prices)
        n_steps = max(1, int(round(horizon_years / dt_years)))
        return _EmpiricalFitted(spot, horizon_years, returns, n_steps)
