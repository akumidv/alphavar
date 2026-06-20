"""Reference split/rejoin — lossless round-trip + layer extraction (T25)."""

import pandas as pd
import pytest

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.reference import apply_reference, split_reference


def _fixture_options(data_path_env) -> pd.DataFrame:
    return pd.read_parquet(f"{data_path_env}/DERIBIT/BTC/option/EOD/2025.parquet").reset_index(drop=True)


def test_split_then_apply_is_lossless(monkeypatch):
    import os

    df = _fixture_options(os.environ.get("DATA_PATH", "tests/fixtures/data"))
    rebuilt = apply_reference(split_reference(df))
    assert set(rebuilt.columns) == set(df.columns)
    pd.testing.assert_frame_equal(rebuilt[df.columns], df, check_dtype=False, check_like=False)


def test_asset_meta_extracted():
    import os

    df = _fixture_options(os.environ.get("DATA_PATH", "tests/fixtures/data"))
    split = split_reference(df)
    assert split.asset.asset_code == "BTC"
    assert split.asset.instrument_kind == "option"


def test_constant_columns_leave_the_time_series():
    import os

    df = _fixture_options(os.environ.get("DATA_PATH", "tests/fixtures/data"))
    split = split_reference(df)
    # asset-level + contract-ref columns are gone from the slim quotes …
    assert OptionsTerm.INSTRUMENT_KIND not in split.quotes.columns
    assert OptionsTerm.EXCH_SYMBOL not in split.quotes.columns
    # … and the contract reference is deduplicated (one row per contract, < quote rows).
    assert OptionsTerm.EXCH_SYMBOL in split.contracts.columns
    assert len(split.contracts) < len(df)
    # the slim frame is smaller in memory than the wide one.
    assert split.quotes.memory_usage(deep=True).sum() < df.memory_usage(deep=True).sum()


def _toy(asset_codes, kinds):
    n = len(asset_codes)
    ts = pd.Timestamp("2025-01-01", tz="UTC")
    return pd.DataFrame(
        {
            OptionsTerm.ASSET_CODE: asset_codes,
            OptionsTerm.INSTRUMENT_KIND: kinds,
            OptionsTerm.EXPIRATION_DATE: [ts] * n,
            OptionsTerm.STRIKE: [100.0] * n,
            OptionsTerm.OPTION_RIGHT: ["call"] * n,
            OptionsTerm.PRICE: [1.0] * n,
        }
    )


def test_multiple_assets_rejected():
    with pytest.raises(ValueError, match="one asset_code"):
        split_reference(_toy(["BTC", "ETH"], ["option", "option"]))


def test_non_constant_asset_level_rejected():
    with pytest.raises(ValueError, match="not constant"):
        split_reference(_toy(["BTC", "BTC"], ["option", "future"]))
