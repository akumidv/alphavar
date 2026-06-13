import pandas as pd
import pytest

from alphavar.core.dictionary import Col, column_names, assert_unique
from alphavar.options.dictionary import OptionsCol, OPTION_COLUMN_DEPENDENCIES


def test_col_members_are_plain_strings():
    # R4.3: a registry member IS the column label, no .nm, no str subclass wrapper.
    assert Col.PRICE == "price"
    assert type(Col.PRICE) is str
    assert Col.ASSET_CODE == "asset_code"


def test_options_inherits_core():
    assert OptionsCol.PRICE == Col.PRICE          # inherited core name
    assert OptionsCol.STRIKE == "strike"          # domain name


def test_usable_directly_as_dataframe_label():
    df = pd.DataFrame({Col.PRICE: [1.0], OptionsCol.STRIKE: [100.0]})
    assert list(df.columns) == ["price", "strike"]
    assert list(df.drop(columns=[Col.PRICE]).columns) == ["strike"]


def test_registry_names_unique():
    assert_unique(OptionsCol)            # must not raise (R4.3 @enum.unique guarantee)


def test_assert_unique_detects_duplicates():
    class Dup:
        A = "x"
        B = "x"
    with pytest.raises(ValueError, match="Duplicate"):
        assert_unique(Dup)


def test_column_names_includes_core_and_domain():
    names = column_names(OptionsCol)
    assert "price" in names          # core
    assert "strike" in names         # domain
    assert "exch_mark_price" in names


def test_dependencies_reference_registry_names():
    # keys/values are registry strings, not literals
    assert OPTION_COLUMN_DEPENDENCIES[OptionsCol.INTRINSIC_VALUE] == [OptionsCol.UNDERLYING_PRICE]
    assert OPTION_COLUMN_DEPENDENCIES[OptionsCol.TIMED_VALUE] == [OptionsCol.INTRINSIC_VALUE]
