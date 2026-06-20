"""HAR-RV volatility forecast (Corsi 2009) (T27).

Heterogeneous Auto-Regressive realized-variance model: ``RV_t = c + β_d·RV^{(d)} + β_w·RV^{(w)} +
β_m·RV^{(m)} + ε`` over daily / weekly (5) / monthly (22) averages of past realized variance. With
EOD data the per-step squared log return ``r²`` is used as the realized-variance proxy; the
one-step regression is iterated forward ``round(H/dt)`` steps and the average forecast variance is
annualized. Short histories (< monthly window) fall back to trailing realized vol.

# 4VERIFY (owner, D2): the HAR design (d/w/m = 1/5/22 step averages), the RV = r² proxy, the OLS
# fit (np.linalg.lstsq), the iterated multi-step forecast, and √(mean forecast var / dt).
"""
from __future__ import annotations

import numpy as np

from alphavar.options.lib.forecast._base import ForecastModel, ForecastTarget
from alphavar.options.lib.forecast.vol._point import PointVol

_D, _W, _M = 1, 5, 22  # daily / weekly / monthly windows, in steps


def _agg(buffer: np.ndarray | list, window: int) -> float:
    return float(np.mean(np.asarray(buffer)[-window:]))


def _features(buffer: np.ndarray | list) -> np.ndarray:
    return np.array([1.0, _agg(buffer, _D), _agg(buffer, _W), _agg(buffer, _M)])


class HarVol(ForecastModel):
    """HAR-RV realized-variance regression; analytic point forecast (iterated multi-step)."""

    name = "har"
    target = ForecastTarget.VOL
    supports = frozenset({"analytic"})

    def fit(self, prices: np.ndarray, dt_years: float, horizon_years: float) -> PointVol:
        returns, _ = self._log_returns(prices)
        ref = float(np.sqrt(self._step_var(returns) / dt_years))
        rv = returns * returns  # realized-variance proxy
        n_steps = max(1, int(round(horizon_years / dt_years)))

        if rv.size < _M + 2:  # not enough for the monthly window + regression rows
            return PointVol(self.name, ref, horizon_years, ref_vol=ref)

        design = np.array([_features(rv[:t]) for t in range(_M, rv.size)])
        target = rv[_M:]
        coef, *_ = np.linalg.lstsq(design, target, rcond=None)

        buffer = list(rv)
        forecasts = []
        for _ in range(n_steps):
            rv_hat = max(float(_features(buffer) @ coef), 0.0)
            buffer.append(rv_hat)
            forecasts.append(rv_hat)
        vol = float(np.sqrt(max(float(np.mean(forecasts)), 0.0) / dt_years))
        return PointVol(self.name, vol, horizon_years, ref_vol=ref)
