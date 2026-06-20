"""Boundary validation at the exchange→storage seam (T23.5)."""

import pandas as pd
import pytest
from pandera.errors import SchemaErrors

from alphavar.core.dictionary import InstrumentKind
from alphavar.options.dictionary import OptionRight, OptionsTerm
from alphavar.options.etl.etl_class import AssetBookData, validate_book_data


def _options_frame(option_right=OptionRight.CALL.value):
    ts = pd.Timestamp("2025-01-01", tz="UTC")
    return pd.DataFrame(
        {
            OptionsTerm.ASSET_CODE: ["BTC", "BTC"],
            OptionsTerm.INSTRUMENT_KIND: [InstrumentKind.OPTION.value] * 2,
            OptionsTerm.TIMESTAMP: [ts, ts],
            OptionsTerm.EXPIRATION_DATE: [ts + pd.Timedelta(days=30)] * 2,
            OptionsTerm.STRIKE: [100.0, 110.0],
            OptionsTerm.OPTION_RIGHT: [option_right, option_right],
            OptionsTerm.PRICE: [1.5, float("nan")],  # price is nullable (interim / no quote yet)
        }
    )


def _book(options):
    return AssetBookData(asset_name="BTC", request_timestamp=pd.Timestamp.now(tz="UTC"),
                         options=options, futures=None, spot=None)


def test_valid_book_passes_through():
    book = _book(_options_frame())
    assert validate_book_data(book) is book  # returned unchanged


def test_none_kinds_are_skipped():
    assert validate_book_data(_book(None)) is not None  # no frames → nothing to validate


def test_bad_option_right_is_rejected():
    bad = _options_frame(option_right="banana")  # not in {call, put}
    with pytest.raises(SchemaErrors):
        validate_book_data(_book(bad))


def test_disabled_validation_is_a_noop(monkeypatch):
    # ALPHAVAR_VALIDATE=0 short-circuits validate() → even a bad frame passes.
    import alphavar.options.schemas as schemas

    monkeypatch.setattr(schemas, "_DISABLED", True)
    bad = _options_frame(option_right="banana")
    assert validate_book_data(_book(bad)) is not None
