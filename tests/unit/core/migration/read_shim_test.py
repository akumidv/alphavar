"""T23.6 read-shim: `rename_legacy_columns` maps legacy parquet column names to the current
dictionary on load, idempotently (no-op on already-current frames)."""

import pandas as pd

from alphavar.core.migration import rename_legacy_columns


def test_renames_legacy_names_and_source_prefix():
    df = pd.DataFrame(
        {
            "exhchange_mark_price": [1.0],  # historical double typo
            "exchange_mark_iv": [0.5],
            "original_timestamp": [pd.Timestamp("2025-01-01", tz="UTC")],
            "source_ask": [2.0],  # raw (pre-currency-conversion) value
            "price": [3.0],  # already current -> untouched
        }
    )
    out = rename_legacy_columns(df)
    assert set(out.columns) == {"exch_mark_price", "exch_mark_iv", "exch_timestamp", "ask_raw", "price"}


def test_idempotent_on_current_frame():
    df = pd.DataFrame({"exch_mark_price": [1.0], "exch_timestamp": [2], "price": [3.0]})
    assert list(rename_legacy_columns(df).columns) == list(df.columns)
    # double application is stable
    assert list(rename_legacy_columns(rename_legacy_columns(df)).columns) == list(df.columns)
