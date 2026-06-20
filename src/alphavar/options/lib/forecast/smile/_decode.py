"""θ → smile decode + multivariate-normal sampling for smile forecasting (T27 iteration 3).

A forecast SVI parameter vector ``θ = (a, b, ρ, m, σ)`` is decoded into a ``SmileResult`` at a
target tenor, reusing the raw-SVI total-variance form ``_raw_w``. Decoded params are lightly clamped
to the SVI domain (b≥0, |ρ|<1, σ>0); ``w(k)`` is floored at 0 by the predictor (full butterfly
no-arb is then checked on the expected smile via ``SmileResult.is_butterfly_free``).

# 4VERIFY (owner, D2): the decode (k=ln(K/F) convention inherited, σ(k)=√(w(k)/τ_target), domain
# clamp) and the PSD multivariate-normal sampler (eigh, negative-eigenvalue clip).
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.pricer.smile import SmileResult, make_smile_model
from alphavar.options.lib.pricer.smile.svi import _raw_w

_RHO_CAP = 0.999


def decode_smile(theta: np.ndarray, param_names: tuple[str, ...], t_years: float) -> SmileResult:
    """Build a ``SmileResult`` at tenor ``t_years`` from an SVI parameter vector ``θ``."""
    p = dict(zip(param_names, (float(x) for x in theta), strict=True))
    a = p["a"]
    b = max(p["b"], 0.0)
    rho = float(np.clip(p["rho"], -_RHO_CAP, _RHO_CAP))
    m = p["m"]
    sigma = abs(p["sigma"])
    t = max(float(t_years), 1e-12)

    def predict(kk: np.ndarray) -> np.ndarray:
        return np.sqrt(np.maximum(_raw_w(np.asarray(kk, dtype=float), a, b, rho, m, sigma), 0.0) / t)

    return SmileResult(make_smile_model("svi"), {"a": a, "b": b, "rho": rho, "m": m, "sigma": sigma}, t, predict)


def sample_mvn(mean: np.ndarray, cov: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Draw ``n`` samples from ``N(mean, cov)`` via a PSD-safe eigendecomposition (no scipy)."""
    mean = np.asarray(mean, dtype=float)
    cov = np.atleast_2d(np.asarray(cov, dtype=float))
    vals, vecs = np.linalg.eigh(cov)
    vals = np.clip(vals, 0.0, None)  # cov may be low-rank (PCA) or have tiny negative round-off
    scale = vecs * np.sqrt(vals)  # (p, p)
    z = rng.standard_normal((int(n), mean.size))
    return mean + z @ scale.T
