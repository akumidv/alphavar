"""Pure-numpy distribution helpers for forecast results (no scipy — repo convention, T27).

``norm_ppf`` is the inverse standard-normal CDF (Acklam's rational approximation,
``|abs err| < 1.15e-9``); the forward CDF already exists as ``pricer.black_scholes.norm_cdf``
(exact via ``math.erf``). ``LogNormalTerminal`` is the terminal-value distribution of the
log-normal price models (``random_walk`` / ``gbm``): ``S_T = exp(μ + σ·Z)``.

# 4VERIFY (owner, D2): the Acklam coefficients / branch points and the lognormal moments
# (ppf(q) = exp(μ + σ·Φ⁻¹(q)), mean = exp(μ + ½σ²)). Pinned by a round-trip vs ``norm_cdf``
# and reference quantiles in tests/unit/options/lib/forecast/stats_test.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

# Acklam (2003) inverse-normal-CDF rational approximation coefficients.
_A = (
    -3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
    1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00,
)
_B = (
    -5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
    6.680131188771972e01, -1.328068155288572e01,
)
_C = (
    -7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
    -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00,
)
_D = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00)
_P_LOW = 0.02425
_P_HIGH = 1.0 - _P_LOW


def norm_ppf(q: np.ndarray | float) -> np.ndarray | float:
    """Inverse standard-normal CDF Φ⁻¹(q), ``q ∈ (0, 1)`` (Acklam; ``|abs err| < 1.15e-9``).

    Vectorized; values of ``q`` outside ``(0, 1)`` return NaN.
    """
    q = np.asarray(q, dtype=float)
    scalar = q.ndim == 0
    q = np.atleast_1d(q)
    out = np.full(q.shape, np.nan, dtype=float)

    lo = (q > 0.0) & (q < _P_LOW)
    if np.any(lo):
        r = np.sqrt(-2.0 * np.log(q[lo]))
        out[lo] = (((((_C[0] * r + _C[1]) * r + _C[2]) * r + _C[3]) * r + _C[4]) * r + _C[5]) / (
            (((_D[0] * r + _D[1]) * r + _D[2]) * r + _D[3]) * r + 1.0
        )
    mid = (q >= _P_LOW) & (q <= _P_HIGH)
    if np.any(mid):
        r = q[mid] - 0.5
        rr = r * r
        out[mid] = (((((_A[0] * rr + _A[1]) * rr + _A[2]) * rr + _A[3]) * rr + _A[4]) * rr + _A[5]) * r / (
            ((((_B[0] * rr + _B[1]) * rr + _B[2]) * rr + _B[3]) * rr + _B[4]) * rr + 1.0
        )
    hi = (q > _P_HIGH) & (q < 1.0)
    if np.any(hi):
        r = np.sqrt(-2.0 * np.log(1.0 - q[hi]))
        out[hi] = -(((((_C[0] * r + _C[1]) * r + _C[2]) * r + _C[3]) * r + _C[4]) * r + _C[5]) / (
            (((_D[0] * r + _D[1]) * r + _D[2]) * r + _D[3]) * r + 1.0
        )
    return float(out[0]) if scalar else out


class TerminalDistribution(ABC):
    """A closed-form distribution of a target's terminal value at the horizon."""

    @abstractmethod
    def mean(self) -> float:
        """Expected terminal value."""

    @abstractmethod
    def ppf(self, q: np.ndarray | float) -> np.ndarray | float:
        """Quantile (inverse CDF) at probability ``q``."""

    @abstractmethod
    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Draw ``n`` terminal values."""


class DegenerateTerminal(TerminalDistribution):
    """A point mass at ``value`` — a deterministic (point) forecast as a degenerate distribution."""

    def __init__(self, value: float):
        self.value = float(value)

    def mean(self) -> float:
        return self.value

    def ppf(self, q: np.ndarray | float) -> np.ndarray | float:
        q = np.asarray(q, dtype=float)
        return self.value if q.ndim == 0 else np.full(q.shape, self.value)

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return np.full(int(n), self.value)


class LogNormalTerminal(TerminalDistribution):
    """``S_T = exp(meanlog + sdlog·Z)``, ``Z ~ N(0, 1)`` — the random_walk / gbm terminal price."""

    def __init__(self, meanlog: float, sdlog: float):
        self.meanlog = float(meanlog)
        self.sdlog = max(float(sdlog), 0.0)

    def mean(self) -> float:
        return float(np.exp(self.meanlog + 0.5 * self.sdlog * self.sdlog))

    def ppf(self, q: np.ndarray | float) -> np.ndarray | float:
        return np.exp(self.meanlog + self.sdlog * norm_ppf(q))

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return np.exp(self.meanlog + self.sdlog * rng.standard_normal(int(n)))
