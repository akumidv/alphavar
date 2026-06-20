"""Mean-reverting AR(1) price model on the log-price (T27 it.5).

``x_t = ln S_t`` follows a Gaussian AR(1): ``x_t = c + φ·x_{t-1} + ε_t``, ``ε ~ N(0, σ_ε²)``,
estimated by OLS (``lstsq`` on ``[1, x_{t-1}]``). The long-run mean is ``μ = c/(1−φ)``; ``|φ|<1``
is mean-reverting (``φ→1`` is the random walk). The ``n``-step-ahead terminal is **still Gaussian**
in log-space (a linear recursion driven by Gaussian shocks), so the price terminal is **log-normal**
— it reuses ``LogNormalPrice`` (analytic + MC) with

    meanlog = μ + φ^n·(x_T − μ),   var = σ_ε²·(1 − φ^{2n})/(1 − φ²),   n = round(H/dt).

# 4VERIFY (owner, D2): the OLS AR(1) estimator (c, φ, σ_ε² with dof = m−2), the φ clip to (−cap,
# cap) for a finite stationary variance, and the n-step mean/variance recursion above (note the
# variance → σ_ε²/(1−φ²) stationary limit and → n·σ_ε² as φ→1).
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import ForecastModel, ForecastTarget
from alphavar.options.lib.forecast.price._lognormal import LogNormalPrice

_PHI_CAP = 0.9999  # keep |φ| < 1 so the n-step variance (1−φ^{2n})/(1−φ²) stays finite


class Ar1Price(ForecastModel):
    """Mean-reverting AR(1) on log-price; log-normal terminal (analytic + MC)."""

    name = "ar1"
    target = ForecastTarget.PRICE
    supports = frozenset({"analytic", "montecarlo"})

    def fit(self, prices: np.ndarray, dt_years: float, horizon_years: float) -> LogNormalPrice:
        p = np.asarray(prices, dtype=float)
        p = p[np.isfinite(p) & (p > 0.0)]
        if p.size < 3:
            raise ValueError("need at least 3 positive finite prices to fit an AR(1) model")
        x = np.log(p)
        x_lag, x_now = x[:-1], x[1:]
        basis = np.vstack([np.ones_like(x_lag), x_lag]).T
        coef, *_ = np.linalg.lstsq(basis, x_now, rcond=None)
        c, phi = float(coef[0]), float(np.clip(coef[1], -_PHI_CAP, _PHI_CAP))
        resid = x_now - (c + phi * x_lag)
        m = x_lag.size
        sigma2_eps = float(resid @ resid) / max(m - 2, 1)
        mu = c / (1.0 - phi)  # long-run mean (|φ| < 1 by the clip)

        n = max(1, int(round(horizon_years / dt_years)))
        phi_n = phi**n
        meanlog = mu + phi_n * (x[-1] - mu)
        var = sigma2_eps * (1.0 - phi ** (2 * n)) / (1.0 - phi * phi)
        return LogNormalPrice(self.name, float(p[-1]), horizon_years, meanlog, float(np.sqrt(max(var, 0.0))))
