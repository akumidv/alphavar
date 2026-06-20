"""T23.1 equivalence (D2): prove the plain-string dictionary reproduces the deleted
``OptionsColumns``/``FuturesColumns``/``SpotColumns`` enums.

The golden values below are the pre-migration enum contents, recovered verbatim from
``git show 46c3a1f~1:src/alphavar/options/dictionary/_dataframe_columns.py`` (the commit
before T23.1). These tests pin the new structures to that golden so the migration is
verifiable at a glance and can never silently regress.
"""

from alphavar.options.dictionary import FUTURES_COLUMN_NAMES, SPOT_COLUMN_NAMES, OptionsTerm
from alphavar.options.lib.normalization.timeframe_resample import (
    DEFAULT_RESAMPLE_MODEL,
    RESAMPLE_SORT_COLUMNS,
)

# --- pre-T23.1 golden (column value -> resample_func, None entries already excluded) ---
_PRE_T23_1_RESAMPLE = {
    "timestamp": "last", "strike": "last", "expiration_date": "last", "option_right": "last",
    "price": "last", "ask": "last", "bid": "last", "open_interest": "last", "volume": "last",
    "volume_premium": "last", "volume_notional": "last", "underlying_expiration_date": "last",
    "exch_mark_price": "last", "exch_mark_iv": "last",
    "open": "first", "close": "last", "high": "max", "low": "min",
    "request_timestamp": "last", "exch_timestamp": "last", "last": "last",
    "underlying_price": "last", "intrinsic_value": "last", "timed_value": "last", "price_status": "last",
    "mark_price": "last", "mark_iv": "last",  # intentionally dropped in T23.1 (unused, R4.2/T23.6)
    "iv": "mean", "delta": "mean", "gamma": "mean", "vega": "mean", "theta": "mean", "rho": "mean",
    "series_code": "last", "asset_code": "last", "exch_symbol": "last", "instrument_kind": "last",
    "underlying_asset_code": "last", "underlying_asset_class": "last", "base_asset_code": "last",
    "title": "last", "option_style": "last", "currency": "last",
}
# The only columns intentionally removed from the model in T23.1.
_DROPPED_COLUMNS = {"mark_price", "mark_iv"}

_PRE_T23_1_FUTURES_NMS = {
    "timestamp", "expiration_date", "price", "ask", "bid", "open_interest", "volume",
    "volume_notional", "open", "close", "high", "low", "request_timestamp", "exch_timestamp",
    "last", "low_24", "high_24", "series_code", "base_asset_code", "instrument_kind",
    "asset_code", "underlying_asset_class", "underlying_asset_code", "title",
}
_PRE_T23_1_SPOT_NMS = {
    "timestamp", "price", "ask", "bid", "open_interest", "volume", "volume_notional",
    "asset_code", "instrument_kind", "title", "open", "close", "high", "low",
    "request_timestamp", "exch_timestamp",
}


def test_resample_model_matches_pre_t23_1_enum():
    """DEFAULT_RESAMPLE_MODEL == the old enum's resample map, minus the two dropped columns."""
    expected = {col: func for col, func in _PRE_T23_1_RESAMPLE.items() if col not in _DROPPED_COLUMNS}
    assert DEFAULT_RESAMPLE_MODEL == expected


def test_dropped_resample_columns_are_gone():
    """mark_price/mark_iv were the only removals — guard against accidental re-add or other drops."""
    assert _DROPPED_COLUMNS.isdisjoint(DEFAULT_RESAMPLE_MODEL)
    assert set(_PRE_T23_1_RESAMPLE) - set(DEFAULT_RESAMPLE_MODEL) == _DROPPED_COLUMNS


def test_futures_column_membership_matches_pre_t23_1_enum():
    assert set(FUTURES_COLUMN_NAMES) == _PRE_T23_1_FUTURES_NMS


def test_spot_column_membership_matches_pre_t23_1_enum():
    assert set(SPOT_COLUMN_NAMES) == _PRE_T23_1_SPOT_NMS


# --- Type B (intentional behavior change, D2): the resample sort columns ---
def test_resample_sort_columns_include_all_three_timestamps():
    """Pins the T23.1 fix: the prior list mixed a `.nm` string with two bare enum members,
    so `exch_timestamp`/`request_timestamp` never matched and were silently dropped from the
    sort. They are now real column names, giving a deterministic multi-key sort. This is an
    intentional behavior change — owner-approved via the D2 ledger."""
    assert RESAMPLE_SORT_COLUMNS == [
        OptionsTerm.TIMESTAMP,
        OptionsTerm.EXCH_TIMESTAMP,
        OptionsTerm.REQUEST_TIMESTAMP,
    ]
