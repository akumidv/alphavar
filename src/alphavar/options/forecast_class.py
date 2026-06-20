"""Forecast facade component (R3, T27): distributions of a target at a future horizon.

Aggregated by ``Option`` over the shared ``OptionsData`` (like pricer / validation). Pure models
and engines live in ``options.lib.forecast``; this class only selects the input series / θ history
and wires it in. Targets: **price** (``random_walk`` / ``gbm`` / ``garch``), **vol** (``ewma`` /
``garch`` / ``har`` / ``realized``), **smile** (SVI-θ ``param_rw`` / ``param_var`` / ``param_pca``,
maturity ``fixed_expiration`` / ``constant_maturity``) and **surface** (``svi_surface`` /
``svi_surface_var`` / ``pca_factor`` over constant-maturity nodes) × engines ``analytic`` /
``montecarlo``. Horizon is calendar ACT/365 (a ``pd.Timestamp`` = an expiration).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.forecast import (
    ForecastResult,
    ForecastTarget,
    make_engine,
    make_forecast_model,
    to_horizon_years,
)
from alphavar.options.lib.forecast._series import (
    front_price_series,
    futures_price_series,
    median_dt_years,
    underlying_price_series,
)
from alphavar.options.lib.forecast.smile import (
    MaturityConvention,
    SmileForecast,
    build_theta_history,
    default_expiration,
    make_smile_engine,
    make_smile_forecast_model,
    resolve_maturity,
)
from alphavar.options.lib.forecast.surface import (
    DEFAULT_TENOR_NODES,
    SurfaceForecast,
    constant_maturity_theta_history,
    make_surface_engine,
    make_surface_forecast_model,
)
from alphavar.options.option_data_class import OptionsData

_DAYS_PER_YEAR = 365.0


class OptionsForecast:
    """Distributional forecasts over ``OptionsData`` (T27)."""

    def __init__(self, data: OptionsData):
        self.data = data

    def price(
        self,
        horizon: pd.Timestamp | pd.Timedelta | float,
        model: str = "gbm",
        engine: str = "montecarlo",
        source: str = "future",
        expiration: pd.Timestamp | None = None,
        n: int = 10000,
        seed: int | None = None,
    ) -> ForecastResult:
        """Forecast the underlying price at ``horizon`` as a distributional ``ForecastResult``.

        ``horizon`` — calendar ACT/365: a ``float`` is days, a ``pd.Timestamp`` is an expiration
        date (auto time-to-horizon). ``model`` — ``random_walk`` / ``gbm`` / ``garch`` / ``ar1``
        (mean-reverting) / ``empirical`` (model-free resampled returns). ``engine`` — ``montecarlo``
        (default) / ``analytic`` (not for ``garch`` / ``empirical``) / ``bootstrap`` (``empirical``
        only). ``source`` — which series to fit: ``future`` (a ``df_fut`` series, default the
        most-populated ``expiration``), ``front`` (rolled continuous front contract, back-adjusted),
        each falling back to ``underlying`` when there is no futures data, or ``underlying``
        (per-timestamp ``underlying_price`` on the options history).
        """
        return self._forecast(ForecastTarget.PRICE, horizon, model, engine, source, expiration, n, seed)

    def vol(
        self,
        horizon: pd.Timestamp | pd.Timedelta | float,
        model: str = "ewma",
        engine: str = "analytic",
        source: str = "future",
        expiration: pd.Timestamp | None = None,
        n: int = 10000,
        seed: int | None = None,
    ) -> ForecastResult:
        """Forecast the annualized volatility over ``horizon`` as a ``ForecastResult``.

        ``model`` — ``ewma`` (RiskMetrics, default) / ``garch`` / ``har`` / ``realized``. ``engine`` —
        ``analytic`` (point forecast, default); ``garch`` also supports ``montecarlo`` (distribution
        of realized vol across paths). ``source`` / ``expiration`` as in ``price``. The result's
        ``change`` is vs the trailing realized vol.
        """
        return self._forecast(ForecastTarget.VOL, horizon, model, engine, source, expiration, n, seed)

    def smile(
        self,
        horizon: pd.Timestamp | pd.Timedelta | float,
        expiration: pd.Timestamp | None = None,
        model: str = "param_rw",
        engine: str = "montecarlo",
        maturity: str = "fixed_expiration",
        smile_model: str = "svi",
        n: int = 10000,
        seed: int | None = None,
        n_components: int = 3,
    ) -> SmileForecast:
        """Forecast one expiration's volatility smile at ``horizon`` as a ``SmileForecast``.

        The SVI parameter vector θ=(a,b,ρ,m,σ) of ``expiration`` (default the most-populated one) is
        calibrated per timestamp over history and forecast forward; the terminal θ is decoded back to
        a smile at the target tenor τ = E − (as_of + horizon). ``model`` — ``param_rw`` (driftless
        RW, default) / ``param_var`` (mean-reverting VAR(1)) / ``param_pca`` (PCA-reduced RW).
        ``engine`` — ``montecarlo`` (σ(k) quantile bands, default) or ``analytic`` (expected smile).
        ``maturity`` — ``fixed_expiration`` (built); ``constant_maturity`` is planned with the
        surface iteration. ``horizon`` is calendar ACT/365 (a ``float`` = days).
        """
        maturity = resolve_maturity(maturity)
        df_hist = self.data.df_hist
        chosen_exp = default_expiration(df_hist) if expiration is None else pd.Timestamp(expiration)
        as_of = df_hist[OptionsTerm.TIMESTAMP].max()
        horizon_years = to_horizon_years(horizon, as_of)
        target_at = as_of + pd.Timedelta(days=horizon_years * _DAYS_PER_YEAR)
        t_target = (chosen_exp - target_at).total_seconds() / (_DAYS_PER_YEAR * 86400.0)
        if t_target <= 0.0:
            raise ValueError(
                f"expiration {chosen_exp.date()} is at/before the horizon ({target_at.date()}); "
                "the smile has expired by then — choose a later expiration or a shorter horizon"
            )

        if maturity is MaturityConvention.CONSTANT_MATURITY:
            # B: model the θ of a single fixed tenor (the target tenor), interpolated across
            # expirations per timestamp — dynamically correct (no tenor roll-down contamination).
            theta, timestamps, _ = constant_maturity_theta_history(df_hist, np.array([t_target]), smile_model)
        else:
            # A: model one expiration's θ and present it at the target tenor (mixes tenors).
            theta, timestamps, _ = build_theta_history(df_hist, chosen_exp, smile_model)
        dt_years = median_dt_years(timestamps)

        forecaster = make_smile_forecast_model(model, n_components=n_components)
        if engine not in forecaster.supports:
            raise ValueError(
                f"model {model!r} does not support engine {engine!r}; supports {sorted(forecaster.supports)}"
            )
        fitted = forecaster.fit(theta, dt_years, horizon_years, t_target)
        return make_smile_engine(engine, n=n, seed=seed).run(fitted)

    def surface(
        self,
        horizon: pd.Timestamp | pd.Timedelta | float,
        tenor_nodes=None,
        model: str = "svi_surface",
        engine: str = "montecarlo",
        smile_model: str = "svi",
        n: int = 10000,
        seed: int | None = None,
        n_components: int = 5,
    ) -> SurfaceForecast:
        """Forecast the whole volatility surface at ``horizon`` as a ``SurfaceForecast``.

        The surface is represented as SVI θ at constant-maturity ``tenor_nodes`` (default
        1w/2w/1m/2m/3m), built per timestamp by interpolating total variance across expirations; the
        stacked θ is forecast forward and decoded back to a surface (σ(k,τ) with tenor inter-/
        extrapolation). ``model`` — ``svi_surface`` (node-wise RW, default) / ``svi_surface_var``
        (VAR(1)) / ``pca_factor`` (PCA-reduced). ``engine`` — ``montecarlo`` (σ(k,τ) bands, default) /
        ``analytic``. ``horizon`` is calendar ACT/365.
        """
        nodes = DEFAULT_TENOR_NODES if tenor_nodes is None else tenor_nodes
        theta, timestamps, resolved_nodes = constant_maturity_theta_history(self.data.df_hist, nodes, smile_model)
        as_of = timestamps.max()
        horizon_years = to_horizon_years(horizon, as_of)
        dt_years = median_dt_years(timestamps)

        forecaster = make_surface_forecast_model(model, n_components=n_components)
        if engine not in forecaster.supports:
            raise ValueError(
                f"model {model!r} does not support engine {engine!r}; supports {sorted(forecaster.supports)}"
            )
        # the forecast tenor for each node = its constant maturity (held fixed), so t_target is unused
        # by the stacked process; the decode reads each node at its own node tenor.
        fitted = forecaster.fit(theta, dt_years, horizon_years, t_target=float(resolved_nodes[0]))
        return make_surface_engine(engine, resolved_nodes, n=n, seed=seed).run(fitted)

    def _forecast(
        self,
        target: ForecastTarget,
        horizon: pd.Timestamp | pd.Timedelta | float,
        model: str,
        engine: str,
        source: str,
        expiration: pd.Timestamp | None,
        n: int,
        seed: int | None,
    ) -> ForecastResult:
        prices, timestamps = self._price_series(source, expiration)
        dt_years = median_dt_years(timestamps)
        horizon_years = to_horizon_years(horizon, timestamps.max())

        forecaster = make_forecast_model(target, model)
        if engine not in forecaster.supports:
            raise ValueError(
                f"model {model!r} does not support engine {engine!r}; supports {sorted(forecaster.supports)}"
            )
        fitted = forecaster.fit(prices, dt_years, horizon_years)
        return make_engine(engine, n=n, seed=seed).run(fitted)

    def _price_series(self, source: str, expiration: pd.Timestamp | None):
        if source == "future":
            df_fut = self.data.df_fut
            if df_fut is None or len(df_fut) == 0:
                return underlying_price_series(self.data.df_hist)
            return futures_price_series(df_fut, expiration)
        if source == "underlying":
            return underlying_price_series(self.data.df_hist)
        if source == "front":
            df_fut = self.data.df_fut
            if df_fut is None or len(df_fut) == 0:
                return underlying_price_series(self.data.df_hist)
            return front_price_series(df_fut)
        raise ValueError(f"unknown source {source!r}; use 'future', 'front' or 'underlying'")
