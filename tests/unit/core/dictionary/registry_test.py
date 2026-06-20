import pandas as pd
import pytest

from alphavar.core.dictionary import Term, assert_unique, column_names
from alphavar.options.dictionary import OPTION_COLUMN_DEPENDENCIES, OptionsTerm


def test_col_members_are_plain_strings():
    # R4.3: a registry member IS the column label, no .nm, no str subclass wrapper.
    assert Term.PRICE == "price"
    assert type(Term.PRICE) is str
    assert Term.ASSET_CODE == "asset_code"


def test_options_inherits_core():
    assert OptionsTerm.PRICE == Term.PRICE  # inherited core name
    assert OptionsTerm.STRIKE == "strike"  # domain name


def test_usable_directly_as_dataframe_label():
    df = pd.DataFrame({Term.PRICE: [1.0], OptionsTerm.STRIKE: [100.0]})
    assert list(df.columns) == ["price", "strike"]
    assert list(df.drop(columns=[Term.PRICE]).columns) == ["strike"]


def test_registry_names_unique():
    assert_unique(OptionsTerm)  # must not raise (R4.3 @enum.unique guarantee)


def test_assert_unique_detects_duplicates():
    class Dup:
        A = "x"
        B = "x"

    with pytest.raises(ValueError, match="Duplicate"):
        assert_unique(Dup)


def test_column_names_includes_core_and_domain():
    names = column_names(OptionsTerm)
    assert "price" in names  # core
    assert "strike" in names  # domain
    assert "exch_mark_price" in names


def test_dependencies_reference_registry_names():
    # keys/values are registry strings, not literals
    assert OPTION_COLUMN_DEPENDENCIES[OptionsTerm.INTRINSIC_VALUE] == [OptionsTerm.UNDERLYING_PRICE]
    assert OPTION_COLUMN_DEPENDENCIES[OptionsTerm.TIMED_VALUE] == [OptionsTerm.INTRINSIC_VALUE]
