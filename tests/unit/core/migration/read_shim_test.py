"""T23.6 read-shim: `rename_legacy_columns` maps legacy parquet column names to the current
dictionary on load, idempotently (no-op on already-current frames)."""

import pandas as pd

from alphavar.core.migration import rename_legacy_columns


def test_renames_neutral_legacy_names_and_source_prefix():
    # Core read-shim handles only the domain-neutral renames (identity / kind / price / time).
    df = pd.DataFrame(
        {
            "exchange_price": [1.0],
            "original_timestamp": [pd.Timestamp("2025-01-01", tz="UTC")],
            "source_ask": [2.0],  # raw (pre-currency-conversion) value
            "price": [3.0],  # already current -> untouched
        }
    )
    out = rename_legacy_columns(df)
    assert set(out.columns) == {"exch_price", "exch_timestamp", "ask_raw", "price"}


def test_idempotent_on_current_frame():
    df = pd.DataFrame({"exch_price": [1.0], "exch_timestamp": [2], "price": [3.0]})
    assert list(rename_legacy_columns(df).columns) == list(df.columns)
    # double application is stable
    assert list(rename_legacy_columns(rename_legacy_columns(df)).columns) == list(df.columns)
