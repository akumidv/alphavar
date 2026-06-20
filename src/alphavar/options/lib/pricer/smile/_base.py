"""Smile-model interface + fit result (T21, R5: price/IV as our model output).

A *smile* is the implied-vol curve of one option slice — fixed ``(asset_code, expiration,
timestamp)`` — as a function of log-moneyness ``k = ln(K / F)`` (F = forward = underlying
price). Models parametrize either the vol ``σ(k)`` or the total implied variance
``w(k) = σ(k)²·T``; this base works in ``σ(k)`` and derives ``w`` from it.

Butterfly (static, single-slice) no-arbitrage is checked numerically via Gatheral's ``g(k)``
on the calibrated ``w(k)`` — model-agnostic, so it also guards the quadratic/SABR fits whose
parametrizations are not arbitrage-free by construction.

# 4VERIFY (owner, D2): the smile is the model output that replaces the interim ``exch_*``
# mirroring (T23.6). Reference fits + the no-arb criterion are pinned in the smile tests.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class SmileResult:
    """Calibrated smile for one slice: predicts ``iv(k)`` at any log-moneyness."""

    model: SmileModel
    params: dict[str, float]
    t_years: float
    _predict_iv: object = field(repr=False)  # Callable[[np.ndarray], np.ndarray]

    def iv(self, k: np.ndarray | float) -> np.ndarray:
        """Implied vol σ(k) at log-moneyness ``k`` (≥ 0)."""
        return np.maximum(self._predict_iv(np.asarray(k, dtype=float)), 0.0)

    def total_variance(self, k: np.ndarray | float) -> np.ndarray:
        """Total implied variance w(k) = σ(k)²·T."""
        return self.iv(k) ** 2 * self.t_years

    def butterfly_g(self, k: np.ndarray) -> np.ndarray:
        """Gatheral's ``g(k)`` of the calibrated total-variance curve (≥ 0 ⇔ no butterfly arb).

        g = (1 − k·w'/(2w))² − (w'/2)²·(1/w + 1/4) + w''/2, with w', w'' by central differences.
        """
        k = np.asarray(k, dtype=float)
        w = self.total_variance(k)
        dk = 1e-4
        w_p = (self.total_variance(k + dk) - self.total_variance(k - dk)) / (2 * dk)
        w_pp = (self.total_variance(k + dk) - 2 * w + self.total_variance(k - dk)) / (dk * dk)
        with np.errstate(divide="ignore", invalid="ignore"):
            term1 = (1.0 - k * w_p / (2.0 * w)) ** 2
            term2 = (w_p / 2.0) ** 2 * (1.0 / w + 0.25)
            return term1 - term2 + w_pp / 2.0

    def is_butterfly_free(self, k_grid: np.ndarray | None = None, tol: float = -1e-6) -> bool:
        """True if ``g(k) ≥ tol`` across a dense log-moneyness grid (no static butterfly arb)."""
        if k_grid is None:
            k_grid = np.linspace(-1.5, 1.5, 121)
        g = self.butterfly_g(k_grid)
        return bool(np.all(np.nan_to_num(g, nan=1.0) >= tol))


class SmileModel(ABC):
    """A volatility-smile parametrization. Stateless: ``fit`` returns a ``SmileResult``."""

    name: str

    @abstractmethod
    def fit(self, k: np.ndarray, iv: np.ndarray, t_years: float, weights: np.ndarray | None = None) -> SmileResult:
        """Calibrate to slice points ``(k_i, iv_i)`` at expiry ``t_years``. NaNs are dropped."""

    @staticmethod
    def _clean(k: np.ndarray, iv: np.ndarray, weights: np.ndarray | None):
        """Drop non-finite / non-positive points; return ``(k, iv, weights)`` finite subsets."""
        k = np.asarray(k, dtype=float)
        iv = np.asarray(iv, dtype=float)
        w = np.ones_like(k) if weights is None else np.asarray(weights, dtype=float)
        mask = np.isfinite(k) & np.isfinite(iv) & (iv > 0.0) & np.isfinite(w) & (w > 0.0)
        return k[mask], iv[mask], w[mask]
