import pandas as pd

from alphavar.core.migration import migrate_dataframe

# Core's neutral spec covers only domain-shared concepts (identity / kind / price / time).
# The derivatives renames (option_type, exchange_iv, the underlying link) live with the options
# domain — see tests/unit/options/migration/legacy_columns_test.py.


def _legacy_df():
    return pd.DataFrame(
        {
            "symbol": ["BTC", "BTC"],
            "exchange_symbol": ["BTC-10APR25-66000-C", "BTC-10APR25-66000-P"],
            "kind": ["o", "o"],
            "exchange_price": [0.1, 0.2],
            "original_timestamp": pd.to_datetime(["2025-04-10", "2025-04-10"]),
            "source_last": [0.11, 0.21],
            "price": [0.1, 0.2],
        }
    )


def test_column_renames():
    out = migrate_dataframe(_legacy_df())
    for old in ("symbol", "exchange_symbol", "kind", "exchange_price", "original_timestamp", "source_last"):
        assert old not in out.columns, old
    for new in ("asset_code", "exch_symbol", "instrument_kind", "exch_price", "exch_timestamp", "last_raw"):
        assert new in out.columns, new


def test_value_remap_codes_to_readable():
    out = migrate_dataframe(_legacy_df())
    assert sorted(out["instrument_kind"].unique()) == ["option"]


def test_two_level_identity_split():
    out = migrate_dataframe(_legacy_df())
    assert list(out["asset_code"].unique()) == ["BTC"]  # was symbol
    assert out["exch_symbol"].iloc[0] == "BTC-10APR25-66000-C"  # was exchange_symbol


def test_source_prefix_to_raw_suffix():
    out = migrate_dataframe(_legacy_df())
    assert "last_raw" in out.columns and "source_last" not in out.columns


def test_idempotent():
    once = migrate_dataframe(_legacy_df())
    twice = migrate_dataframe(once)
    assert list(once.columns) == list(twice.columns)
    assert once.equals(twice)
