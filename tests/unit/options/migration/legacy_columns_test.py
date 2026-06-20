"""Options domain migration: the derivatives legacy-column spec (renames + value codes)."""

import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.migration import OPTIONS_SPEC, migrate_options_parquet_tree, rename_legacy_option_columns


def test_domain_read_shim_renames_derivatives_columns():
    # The derivatives legacy names that core (neutral) no longer knows — only the domain shim does.
    df = pd.DataFrame(
        {
            "exhchange_mark_price": [1.0],  # historical double typo
            "exchange_mark_iv": [0.5],
            "exchange_iv": [0.4],
            "option_type": ["c"],
            "original_timestamp": [pd.Timestamp("2025-01-01", tz="UTC")],  # neutral, also handled
            "price": [3.0],
        }
    )
    out = rename_legacy_option_columns(df)
    assert OptionsTerm.EXCH_MARK_PRICE in out.columns
    assert OptionsTerm.EXCH_MARK_IV in out.columns
    assert OptionsTerm.EXCH_IV in out.columns
    assert OptionsTerm.OPTION_RIGHT in out.columns  # option_type -> option_right
    assert OptionsTerm.EXCH_TIMESTAMP in out.columns  # neutral rename still applies


def test_options_spec_extends_core_with_domain_only_mappings():
    # core neutral key present, plus a derivatives key the core spec must NOT carry
    assert OPTIONS_SPEC.renames["exchange_price"] == OptionsTerm.EXCH_PRICE  # from CORE_SPEC
    assert OPTIONS_SPEC.renames["exchange_iv"] == OptionsTerm.EXCH_IV  # from the domain spec


def test_migrate_tree_remaps_domain_value_codes(tmp_path):
    path = tmp_path / "f.parquet"
    pd.DataFrame(
        {
            OptionsTerm.ASSET_CODE: ["BTC"],
            "option_type": ["p"],  # legacy code -> put
            "underlying_asset_type": ["y"],  # legacy code -> crypto
            OptionsTerm.PRICE: [1.0],
        }
    ).to_parquet(path)
    assert migrate_options_parquet_tree(str(tmp_path), apply=True) == 1
    out = pd.read_parquet(path)
    assert out[OptionsTerm.OPTION_RIGHT].iloc[0] == "put"
    assert out[OptionsTerm.UNDERLYING_ASSET_CLASS].iloc[0] == "crypto"
