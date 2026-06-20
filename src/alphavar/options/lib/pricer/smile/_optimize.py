"""Pure-numpy Nelder–Mead simplex minimizer (no scipy in the dependency set, T21).

A small, dependency-free downhill-simplex optimizer for the low-dimensional smile
calibrations (SVI's 2-D outer (m, σ) search; SABR's (α, ρ, ν)). Not a general optimizer —
just robust enough for these smooth 2–3 parameter objectives.

# 4VERIFY (owner, D2): the optimizer is a numerical means, not domain math; what matters is
# that each smile model's objective + bounds are correct (see svi.py / sabr.py).
"""
from __future__ import annotations

from collections.abc import Callable

import numpy as np


def minimize_nelder_mead(
    func: Callable[[np.ndarray], float],
    x0: np.ndarray,
    *,
    step: float | np.ndarray = 0.1,
    max_iter: int = 400,
    tol: float = 1e-8,
) -> tuple[np.ndarray, float]:
    """Minimize ``func`` from ``x0`` by Nelder–Mead. Returns ``(best_x, best_value)``.

    Standard reflection/expansion/contraction/shrink coefficients (1, 2, 0.5, 0.5). The
    initial simplex perturbs each coordinate by ``step``. Stops on a small spread of simplex
    vertex values or ``max_iter``.
    """
    x0 = np.asarray(x0, dtype=float)
    n = x0.size
    steps = np.full(n, step, dtype=float) if np.isscalar(step) else np.asarray(step, dtype=float)

    # build the initial simplex (n+1 vertices)
    simplex = np.vstack([x0] + [x0 + np.eye(n)[i] * steps[i] for i in range(n)])
    values = np.array([func(v) for v in simplex], dtype=float)

    for _ in range(max_iter):
        order = np.argsort(values)
        simplex, values = simplex[order], values[order]
        if abs(values[-1] - values[0]) <= tol * (abs(values[0]) + tol):
            break

        centroid = simplex[:-1].mean(axis=0)  # exclude the worst vertex
        worst = simplex[-1]

        reflected = centroid + 1.0 * (centroid - worst)
        f_ref = func(reflected)
        if values[0] <= f_ref < values[-2]:
            simplex[-1], values[-1] = reflected, f_ref
            continue
        if f_ref < values[0]:  # expand
            expanded = centroid + 2.0 * (centroid - worst)
            f_exp = func(expanded)
            if f_exp < f_ref:
                simplex[-1], values[-1] = expanded, f_exp
            else:
                simplex[-1], values[-1] = reflected, f_ref
            continue
        # contract
        contracted = centroid + 0.5 * (worst - centroid)
        f_con = func(contracted)
        if f_con < values[-1]:
            simplex[-1], values[-1] = contracted, f_con
            continue
        # shrink toward the best vertex
        best = simplex[0]
        simplex = best + 0.5 * (simplex - best)
        values = np.array([func(v) for v in simplex], dtype=float)

    best_idx = int(np.argmin(values))
    return simplex[best_idx], float(values[best_idx])
