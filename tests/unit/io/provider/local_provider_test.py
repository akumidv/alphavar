"""Tests for local provider"""

import datetime
import logging

import pandas as pd

from alphavar.io.provider import AbstractProvider, RequestParameters
from alphavar.io.provider._local_provider import _filter_lower, _filter_upper
from alphavar.options.dictionary import OptionsTerm, Timeframe

# The committed BTC option fixture (DERIBIT/BTC/option/EOD/2025.parquet) holds EOD rows for
# three days; per-day row counts are pinned here for the period-loading semantics (T19).
_DAY_19 = datetime.date(2025, 4, 19)
_DAY_20 = datetime.date(2025, 4, 20)
_DAY_21 = datetime.date(2025, 4, 21)
_ROWS = {_DAY_19: 798, _DAY_20: 764, _DAY_21: 720}
_TOTAL = sum(_ROWS.values())


def test_load_option(exchange_provider, asset_code, provider_params):
    df_opt = exchange_provider.load_options_history(asset_code=asset_code, params=provider_params)
    assert isinstance(df_opt, pd.DataFrame)
    assert all(p_ocl in df_opt.columns for p_ocl in AbstractProvider.options_columns)


def test_load_future(exchange_provider, asset_code, provider_params):
    df_fut = exchange_provider.load_futures_history(asset_code=asset_code, params=provider_params)
    assert isinstance(df_fut, pd.DataFrame)
    assert all(f_col in df_fut.columns for f_col in AbstractProvider.futures_columns)


def _load(provider, asset_code, **kw):
    return provider.load_options_history(asset_code=asset_code, params=RequestParameters(timeframe=Timeframe.EOD, **kw))


def test_period_to_year_int(exchange_provider, asset_code):
    """Only period_to=<year> -> everything through that year (inclusive ceiling)."""
    df = _load(exchange_provider, asset_code, period_to=2025)
    assert len(df) == _TOTAL


def test_period_to_date_is_inclusive_ceiling(exchange_provider, asset_code):
    """Only period_to=<date> -> all rows up to and including that whole day."""
    df = _load(exchange_provider, asset_code, period_to=_DAY_20)
    assert set(df[OptionsTerm.TIMESTAMP].dt.date) == {_DAY_19, _DAY_20}
    assert len(df) == _ROWS[_DAY_19] + _ROWS[_DAY_20]


def test_period_to_datetime_is_inclusive_instant(exchange_provider, asset_code):
    """Only period_to=<datetime> -> rows with timestamp <= that instant (naive bound aligns to the column tz)."""
    df = _load(exchange_provider, asset_code, period_to=datetime.datetime(2025, 4, 20, 12, 0))
    assert set(df[OptionsTerm.TIMESTAMP].dt.date) == {_DAY_19, _DAY_20}  # day 20 EOD is 00:00 <= noon
    assert len(df) == _ROWS[_DAY_19] + _ROWS[_DAY_20]


def test_period_none_loads_all_years(exchange_provider, asset_code):
    """Neither bound -> all stored years."""
    df = _load(exchange_provider, asset_code)
    assert len(df) == _TOTAL


def test_period_date_range_is_inclusive(exchange_provider, asset_code):
    """Both bounds set -> inclusive [from, to] range."""
    df = _load(exchange_provider, asset_code, period_from=_DAY_19, period_to=_DAY_20)
    assert set(df[OptionsTerm.TIMESTAMP].dt.date) == {_DAY_19, _DAY_20}
    assert len(df) == _ROWS[_DAY_19] + _ROWS[_DAY_20]


def test_period_from_date_to_last(exchange_provider, asset_code):
    """Only period_from -> from that day through the last stored data."""
    df = _load(exchange_provider, asset_code, period_from=_DAY_20)
    assert set(df[OptionsTerm.TIMESTAMP].dt.date) == {_DAY_20, _DAY_21}
    assert len(df) == _ROWS[_DAY_20] + _ROWS[_DAY_21]


def test_period_from_year_to_last(exchange_provider, asset_code):
    """Only period_from=<year> -> from that year through the last stored year."""
    df = _load(exchange_provider, asset_code, period_from=2025)
    assert len(df) == _TOTAL


def test_missing_year_in_span_is_skipped_with_warning(exchange_provider, asset_code, caplog):
    """A year file absent inside a requested span is skipped + warned, not fatal."""
    with caplog.at_level(logging.WARNING):
        df = _load(exchange_provider, asset_code, period_from=2024, period_to=2025)
    assert len(df) == _TOTAL  # only 2025 exists; 2024 skipped
    assert any("2024" in rec.message for rec in caplog.records)


# --- intraday floor/ceiling semantics, proven on a synthetic minute-resolution frame ---
# (the committed fixture is EOD-only — all rows at 00:00 — so it can't exercise sub-day bounds).

def _minute_frame() -> pd.DataFrame:
    ts = pd.date_range("2025-04-19 00:00", "2025-04-21 23:59", freq="min", tz="UTC")
    return pd.DataFrame({OptionsTerm.TIMESTAMP: ts})


def test_filter_lower_date_floors_to_minute_zero_of_the_day():
    """period_from=<date> at a minute timeframe -> every minute of that day from 0 onward
    (the floor is the day's 00:00, never the next day); earlier days are excluded."""
    out = _filter_lower(_minute_frame(), OptionsTerm.TIMESTAMP, _DAY_20)
    assert out[OptionsTerm.TIMESTAMP].min() == pd.Timestamp("2025-04-20 00:00", tz="UTC")
    assert set(out[OptionsTerm.TIMESTAMP].dt.date) == {_DAY_20, _DAY_21}


def test_filter_upper_date_ceils_to_last_minute_of_the_day():
    """period_to=<date> at a minute timeframe -> through the day's last minute, not into the next day."""
    out = _filter_upper(_minute_frame(), OptionsTerm.TIMESTAMP, _DAY_20)
    assert out[OptionsTerm.TIMESTAMP].max() == pd.Timestamp("2025-04-20 23:59", tz="UTC")
    assert set(out[OptionsTerm.TIMESTAMP].dt.date) == {_DAY_19, _DAY_20}


def test_filter_datetime_bounds_are_exact_instants():
    """A datetime bound cuts at the exact minute (inclusive), not the whole day."""
    df = _minute_frame()
    lo = _filter_lower(df, OptionsTerm.TIMESTAMP, datetime.datetime(2025, 4, 20, 10, 0))
    assert lo[OptionsTerm.TIMESTAMP].min() == pd.Timestamp("2025-04-20 10:00", tz="UTC")
    hi = _filter_upper(df, OptionsTerm.TIMESTAMP, datetime.datetime(2025, 4, 20, 10, 0))
    assert hi[OptionsTerm.TIMESTAMP].max() == pd.Timestamp("2025-04-20 10:00", tz="UTC")
