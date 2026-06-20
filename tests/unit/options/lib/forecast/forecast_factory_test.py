"""Forecast factory: model/engine selection + planned-vs-unknown errors (T27)."""

import pytest

from alphavar.options.lib.forecast import ForecastTarget, make_engine, make_forecast_model
from alphavar.options.lib.forecast.engine.bootstrap import BootstrapEngine
from alphavar.options.lib.forecast.engine.montecarlo import MonteCarloEngine
from alphavar.options.lib.forecast.price.gbm import GbmPrice


def test_make_price_model_by_name():
    assert isinstance(make_forecast_model(ForecastTarget.PRICE, "gbm"), GbmPrice)
    assert isinstance(make_forecast_model("price", "random_walk").supports, frozenset)


def test_it5_price_models_are_available():
    for name in ("ar1", "empirical"):
        assert make_forecast_model(ForecastTarget.PRICE, name).target is ForecastTarget.PRICE
    assert "bootstrap" in make_forecast_model(ForecastTarget.PRICE, "empirical").supports


def test_unknown_price_model_raises_value_error():
    with pytest.raises(ValueError):
        make_forecast_model(ForecastTarget.PRICE, "nope")


def test_planned_model_and_target_raise_not_implemented():
    for name in ("factor_linear", "var"):  # factor-conditional models still need the input contract
        with pytest.raises(NotImplementedError):
            make_forecast_model(ForecastTarget.PRICE, name)
    with pytest.raises(NotImplementedError):
        make_forecast_model(ForecastTarget.SMILE, "param_rw")


def test_vol_models_are_available():
    for name in ("ewma", "garch", "har", "realized"):
        assert make_forecast_model(ForecastTarget.VOL, name).target is ForecastTarget.VOL


def test_make_engine_default_and_bootstrap():
    assert isinstance(make_engine(), MonteCarloEngine)
    assert make_engine("montecarlo", seed=3).seed == 3
    assert isinstance(make_engine("bootstrap", seed=3), BootstrapEngine)
    with pytest.raises(ValueError):
        make_engine("nope")
