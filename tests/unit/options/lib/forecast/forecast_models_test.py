"""Price forecast models + engines + horizon/result (T27)."""

import numpy as np
import pandas as pd
import pytest

from alphavar.options.lib.forecast import ForecastResult, ForecastTarget, to_horizon_years
from alphavar.options.lib.forecast.engine.analytic import AnalyticEngine
from alphavar.options.lib.forecast.engine.bootstrap import BootstrapEngine
from alphavar.options.lib.forecast.engine.montecarlo import MonteCarloEngine
from alphavar.options.lib.forecast.price.ar1 import Ar1Price
from alphavar.options.lib.forecast.price.empirical import EmpiricalPrice
from alphavar.options.lib.forecast.price.garch import GarchPrice
from alphavar.options.lib.forecast.price.gbm import GbmPrice
from alphavar.options.lib.forecast.price.random_walk import RandomWalkPrice

_DT = 1.0 / 365.0


def _gbm_series(n=750, mu=0.05, sigma=0.4, s0=100.0, seed=0):
    """A synthetic daily GBM price path."""
    rng = np.random.default_rng(seed)
    r = (mu - 0.5 * sigma**2) * _DT + sigma * np.sqrt(_DT) * rng.standard_normal(n)
    return s0 * np.exp(np.cumsum(r))


def _ou_series(n=1500, kappa=5.0, mu_x=4.605170, sigma=0.4, seed=0):
    """A synthetic daily mean-reverting (AR(1)/OU) log-price path around exp(mu_x) ≈ 100."""
    rng = np.random.default_rng(seed)
    x = np.empty(n)
    x[0] = mu_x
    phi = 1.0 - kappa * _DT  # AR(1) coefficient of the discretized OU
    for t in range(1, n):
        x[t] = mu_x + phi * (x[t - 1] - mu_x) + sigma * np.sqrt(_DT) * rng.standard_normal()
    return np.exp(x)


# --- horizon normalization --------------------------------------------------------------------


def test_horizon_days_timedelta_and_expiration_agree():
    as_of = pd.Timestamp("2026-01-01", tz="UTC")
    assert np.isclose(to_horizon_years(30.0, as_of), 30.0 / 365.0)
    assert np.isclose(to_horizon_years(pd.Timedelta(days=30), as_of), 30.0 / 365.0)
    assert np.isclose(to_horizon_years(as_of + pd.Timedelta(days=30), as_of), 30.0 / 365.0)


def test_horizon_must_be_positive():
    as_of = pd.Timestamp("2026-01-01", tz="UTC")
    with pytest.raises(ValueError):
        to_horizon_years(0.0, as_of)
    with pytest.raises(ValueError):
        to_horizon_years(as_of - pd.Timedelta(days=1), as_of)


# --- gbm: analytic ↔ Monte-Carlo --------------------------------------------------------------


def test_gbm_analytic_matches_montecarlo():
    prices = _gbm_series()
    fitted = GbmPrice().fit(prices, _DT, 30.0 / 365.0)
    analytic = AnalyticEngine().run(fitted)
    mc = MonteCarloEngine(n=100_000, seed=1).run(fitted)
    qs = [0.1, 0.5, 0.9]
    assert np.allclose(analytic.quantiles(qs), mc.quantiles(qs), rtol=0.03)
    assert np.isclose(analytic.point(), mc.point(), rtol=0.02)


def test_gbm_longer_horizon_widens_distribution():
    prices = _gbm_series()
    short = GbmPrice().fit(prices, _DT, 10.0 / 365.0).analytic_terminal()
    long = GbmPrice().fit(prices, _DT, 90.0 / 365.0).analytic_terminal()
    assert long.sdlog > short.sdlog


# --- random walk: driftless baseline ----------------------------------------------------------


def test_random_walk_is_driftless():
    prices = _gbm_series(mu=0.5)  # strong drift in the data, ignored by the RW baseline
    result = AnalyticEngine().run(RandomWalkPrice().fit(prices, _DT, 60.0 / 365.0))
    assert np.isclose(result.quantiles(0.5), prices[-1], rtol=1e-9)  # median = spot


# --- garch: MC only ---------------------------------------------------------------------------


def test_garch_runs_montecarlo_and_is_stationary():
    prices = _gbm_series(seed=7)
    fitted = GarchPrice().fit(prices, _DT, 30.0 / 365.0)
    assert fitted.alpha >= 0.0 and fitted.beta >= 0.0 and fitted.alpha + fitted.beta < 1.0
    result = MonteCarloEngine(n=20_000, seed=2).run(fitted)
    assert np.all(result.scenarios() > 0.0)
    assert result.point() > 0.0


def test_garch_has_no_analytic_form():
    fitted = GarchPrice().fit(_gbm_series(), _DT, 30.0 / 365.0)
    assert fitted.analytic_terminal() is None
    with pytest.raises(ValueError):
        AnalyticEngine().run(fitted)


# --- ar1: mean reversion (it.5) ---------------------------------------------------------------


def test_ar1_analytic_matches_montecarlo():
    prices = _ou_series()
    fitted = Ar1Price().fit(prices, _DT, 30.0 / 365.0)
    analytic = AnalyticEngine().run(fitted)
    mc = MonteCarloEngine(n=100_000, seed=1).run(fitted)
    assert np.allclose(analytic.quantiles([0.1, 0.5, 0.9]), mc.quantiles([0.1, 0.5, 0.9]), rtol=0.03)


def test_ar1_reverts_toward_long_run_mean():
    # start the forecast from a level far above the long-run mean ⇒ the terminal median pulls down
    prices = _ou_series()
    spot = prices[-1]
    long_run = float(np.exp(np.mean(np.log(prices))))
    median = Ar1Price().fit(prices, _DT, 120.0 / 365.0).analytic_terminal().ppf(0.5)
    if spot > long_run:
        assert median < spot
    else:
        assert median > spot


# --- empirical: model-free resampling + bootstrap (it.5) --------------------------------------


def test_empirical_montecarlo_distribution_is_positive_and_centered():
    prices = _gbm_series(mu=0.0)  # driftless data ⇒ terminal median near spot
    result = MonteCarloEngine(n=50_000, seed=1).run(EmpiricalPrice().fit(prices, _DT, 20.0 / 365.0))
    assert np.all(result.scenarios() > 0.0)
    assert np.isclose(result.quantiles(0.5), prices[-1], rtol=0.05)


def test_empirical_has_no_analytic_form():
    fitted = EmpiricalPrice().fit(_gbm_series(), _DT, 20.0 / 365.0)
    assert fitted.analytic_terminal() is None
    with pytest.raises(ValueError):
        AnalyticEngine().run(fitted)


def test_empirical_bootstrap_engine_runs_and_is_reproducible():
    fitted = EmpiricalPrice().fit(_gbm_series(seed=3), _DT, 30.0 / 365.0)
    a = BootstrapEngine(n=10_000, seed=7).run(fitted)
    b = BootstrapEngine(n=10_000, seed=7).run(fitted)
    assert np.array_equal(a.scenarios(), b.scenarios())
    assert np.all(a.scenarios() > 0.0)


def test_bootstrap_engine_rejects_models_without_empirical_series():
    with pytest.raises(ValueError):
        BootstrapEngine(seed=0).run(GbmPrice().fit(_gbm_series(), _DT, 30.0 / 365.0))


# --- result views -----------------------------------------------------------------------------


def test_result_change_and_to_frame():
    prices = _gbm_series()
    result = AnalyticEngine().run(GbmPrice().fit(prices, _DT, 30.0 / 365.0))
    assert isinstance(result, ForecastResult)
    assert result.target is ForecastTarget.PRICE
    assert np.isclose(result.change(), result.point() - result.spot)
    frame = result.to_frame(quantiles=(0.05, 0.5, 0.95))
    assert list(frame.columns) == ["quantile", "price", "change"]
    assert np.allclose(frame["change"], frame["price"] - result.spot)
