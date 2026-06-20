"""Quadratic-in-log-moneyness smile: σ(k) = a + b·k + c·k² (T21).

The robust low-data fallback — a plain linear least squares (``np.linalg.lstsq``) on the
basis ``[1, k, k²]``, no iterative calibration. Not arbitrage-free by construction; the
caller checks ``SmileResult.is_butterfly_free`` (Gatheral g(k)) post-fit.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.pricer.smile._base import SmileModel, SmileResult


class QuadraticSmile(SmileModel):
    """σ(k) = a + b·k + c·k² fit by weighted least squares."""

    name = "quadratic"

    def fit(self, k: np.ndarray, iv: np.ndarray, t_years: float, weights: np.ndarray | None = None) -> SmileResult:
        k, iv, w = self._clean(k, iv, weights)
        if k.size < 3:  # underdetermined → flat smile at the (weighted) mean vol
            level = float(np.average(iv, weights=w)) if k.size else float("nan")
            return SmileResult(self, {"a": level, "b": 0.0, "c": 0.0}, t_years, lambda kk: np.full_like(kk, level))

        basis = np.vstack([np.ones_like(k), k, k * k]).T
        sw = np.sqrt(w)
        coef, *_ = np.linalg.lstsq(basis * sw[:, None], iv * sw, rcond=None)
        a, b, c = (float(x) for x in coef)

        def predict(kk: np.ndarray) -> np.ndarray:
            return a + b * kk + c * kk * kk

        return SmileResult(self, {"a": a, "b": b, "c": c}, t_years, predict)
