"""PCA-reduced random walk on the SVI parameter vector θ (T27 iteration 3).

Like ``param_rw`` (driftless, terminal mean = last θ), but the increment covariance is projected
onto its top ``n_components`` principal directions before scaling to the horizon. This denoises a
high-dimensional, collinear θ space (the five raw-SVI parameters are strongly correlated), so the
scenario smiles vary along the dominant modes of historical movement rather than estimation noise.
The terminal covariance is the reduced-rank ``n_steps · Σ_k`` (Σ_k = top-k spectral truncation of
cov(Δθ)); the PSD-safe MVN sampler handles the rank deficiency.

# 4VERIFY (owner, D2): the eigen-truncation of cov(Δθ) to n_components, terminal cov =
# n_steps · Σ_k, driftless mean = last θ.
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast.smile._base import SMILE_PARAM_NAMES, SmileForecastModel, ThetaProcess
from alphavar.options.lib.forecast.smile.param_rw import increment_cov

_DEFAULT_COMPONENTS = 3


class ParamPCA(SmileForecastModel):
    """Driftless random walk on θ restricted to the top principal modes of its increments."""

    name = "param_pca"
    supports = frozenset({"analytic", "montecarlo"})

    def __init__(self, n_components: int = _DEFAULT_COMPONENTS):
        self.n_components = int(n_components)

    def fit(self, theta_history: np.ndarray, dt_years: float, horizon_years: float, t_target: float) -> ThetaProcess:
        theta, p = self._prepare(theta_history)
        n_steps = self._n_steps(horizon_years, dt_years)
        theta0 = theta[-1]

        step_cov = increment_cov(theta)
        vals, vecs = np.linalg.eigh(step_cov)  # ascending eigenvalues
        vals = np.clip(vals, 0.0, None)
        keep = min(self.n_components, p)
        idx = np.argsort(vals)[::-1][:keep]  # top-k modes
        reduced = (vecs[:, idx] * vals[idx]) @ vecs[:, idx].T  # rank-k reconstruction of cov(Δθ)
        cov = n_steps * reduced
        return ThetaProcess(self.name, SMILE_PARAM_NAMES, t_target, horizon_years, theta0, theta0.copy(), cov)
