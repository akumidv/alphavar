"""Migration robustness (ADR 0001): old/mixed/typed files fail loudly, not silently."""

import pandas as pd
import pytest

from alphavar.core.migration.legacy_parquet import MigrationError, migrate_dataframe


def test_mixed_legacy_and_canonical_same_concept_raises():
    # Both legacy 'kind' and canonical 'instrument_kind' for the same concept -> ambiguous.
    df = pd.DataFrame({"symbol": ["BTC"], "kind": ["o"], "instrument_kind": ["option"]})
    with pytest.raises(MigrationError, match="instrument_kind"):
        migrate_dataframe(df)


def test_both_symbol_and_asset_code_raises():
    df = pd.DataFrame({"symbol": ["BTC"], "asset_code": ["BTC"]})
    with pytest.raises(MigrationError, match="asset_code"):
        migrate_dataframe(df)


def test_unparseable_timestamp_type_raises():
    df = pd.DataFrame({"symbol": ["BTC"], "timestamp": ["not-a-date"]})
    with pytest.raises(MigrationError, match="timestamp"):
        migrate_dataframe(df)


def test_epoch_int_timestamp_is_coerced():
    df = pd.DataFrame({"symbol": ["BTC"], "timestamp": pd.to_datetime(["2025-01-01"]).astype("int64")})
    out = migrate_dataframe(df)
    assert pd.api.types.is_datetime64_any_dtype(out["timestamp"])


def test_no_identity_column_raises():
    # No symbol/asset_code/base/exch_symbol -> structure too old to recognize.
    df = pd.DataFrame({"kind": ["o"], "price": [1.0]})
    with pytest.raises(MigrationError, match="identity"):
        migrate_dataframe(df)
