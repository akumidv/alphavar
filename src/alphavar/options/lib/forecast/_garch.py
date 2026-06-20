"""Shared GARCH(1,1) Gaussian-MLE estimation — pure-numpy, used by price & vol models (T27).

Log returns ``r_t = μ + ε_t``, ``ε_t = σ_t·z_t`` (``z ~ N(0,1)``), with
``σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}`` (ω>0, α,β≥0, α+β<1 for stationarity). Estimated by Gaussian
MLE with the pure-numpy ``minimize_nelder_mead`` (no scipy), via an unconstrained reparametrization
(ω = exp; persistence φ and α-share through the logistic ⇒ ω>0, α,β≥0, α+β = φ < 1). Too little
data ⇒ a constant-variance fallback (α = β = 0).

# 4VERIFY (owner, D2): the GARCH(1,1) recursion + Gaussian log-likelihood, the reparam, the
# one-step-ahead σ²_{T+1} seed, and the stationary unconditional variance ω/(1−α−β).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from alphavar.options.lib.pricer.smile._optimize import minimize_nelder_mead

_MIN_RETURNS = 10  # below this, (ω, α, β) is unidentified → constant-variance fallback


@dataclass
class GarchParams:
    """Calibrated GARCH(1,1): mean + (ω, α, β), the one-step-ahead and unconditional variances."""

    mu: float
    omega: float
    alpha: float
    beta: float
    sigma2_next: float  # σ²_{T+1}, one-step-ahead per-step variance
    uncond_var: float  # unconditional per-step variance (ω/(1−α−β) if stationary, else sample var)

    @property
    def persistence(self) -> float:
        """α + β — how slowly variance reverts to ``uncond_var``."""
        return self.alpha + self.beta


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def _unpack(theta: np.ndarray) -> tuple[float, float, float]:
    """(ω, α, β) from the unconstrained vector: ω=exp(θ₀), φ=σ(θ₁), α=φ·σ(θ₂), β=φ−α."""
    omega = float(np.exp(theta[0]))
    phi = _sigmoid(theta[1])  # persistence α+β ∈ (0,1)
    share = _sigmoid(theta[2])  # α's share of the persistence
    alpha = phi * share
    beta = phi - alpha
    return omega, alpha, beta


def _conditional_variances(eps: np.ndarray, omega: float, alpha: float, beta: float, var0: float) -> np.ndarray:
    """σ²_t series (σ²_0 = var0); σ²_t pairs with ε_t (used for the log-likelihood)."""
    sigma2 = np.empty(eps.size, dtype=float)
    s = var0
    for t in range(eps.size):
        sigma2[t] = s
        s = omega + alpha * eps[t] * eps[t] + beta * s
    return sigma2


def _next_variance(eps: np.ndarray, omega: float, alpha: float, beta: float, var0: float) -> float:
    """One-step-ahead conditional variance σ²_{T+1} after the last observed return."""
    s = var0
    for e in eps:
        s = omega + alpha * e * e + beta * s
    return float(s)


def estimate_garch(returns: np.ndarray, min_returns: int = _MIN_RETURNS) -> GarchParams:
    """Fit GARCH(1,1) to ``returns`` by Gaussian MLE; constant-variance fallback if too short."""
    r = np.asarray(returns, dtype=float)
    mu = float(np.mean(r))
    uncond = float(np.var(r, ddof=1)) if r.size > 1 else float(np.var(r))
    if r.size < min_returns or uncond <= 0.0:
        return GarchParams(mu, uncond, 0.0, 0.0, uncond, uncond)

    eps = r - mu

    def neg_log_likelihood(theta: np.ndarray) -> float:
        omega, alpha, beta = _unpack(theta)
        sigma2 = _conditional_variances(eps, omega, alpha, beta, uncond)
        return 0.5 * float(np.sum(np.log(sigma2) + eps * eps / sigma2))

    # start near a typical equity/crypto fit: ω small, persistence ~0.9, α-share ~0.1
    theta0 = np.array([np.log(uncond * 0.1), float(np.log(0.9 / 0.1)), float(np.log(0.1 / 0.9))])
    best, _ = minimize_nelder_mead(neg_log_likelihood, theta0, step=0.5, max_iter=600)
    omega, alpha, beta = _unpack(best)
    sigma2_next = _next_variance(eps, omega, alpha, beta, uncond)
    persistence = alpha + beta
    uncond_var = omega / (1.0 - persistence) if persistence < 1.0 else uncond
    return GarchParams(mu, omega, alpha, beta, sigma2_next, uncond_var)
