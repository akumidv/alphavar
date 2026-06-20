"""Characterization test for the Deribit book normalization (T20 vectorization, D2 Type A).

`DeribitMarket._normalize_book` was rewritten from a row-wise `df.apply(_kind_enrichment,
axis="columns")` (deep-copy per row, the dominant ETL cost) to vectorized masks. This test pins
the new implementation to the *old* row-wise behavior on the recorded full BTC book (a realistic
mix of spot / future / future_combo / option / option_combo), so the refactor is provably
equivalent. The oracle below is the verbatim pre-T20 logic.
"""

# pylint: disable=protected-access
import datetime

import pandas as pd
import pytest

from alphavar.io.exchange._abstract_exchange import AbstractExchange
from alphavar.io.exchange.deribit import (
    COLUMNS_TO_CURRENCY,
    DOT_STRIKE_REGEXP,
    DeribitAssetKind,
    DeribitExchange,
)
from alphavar.io.exchange.exchange_exception import InstrumentParseError
from alphavar.options.dictionary import OptionsTerm, OptionsType
from alphavar.options.lib.normalization import (
    fill_option_price,
    normalize_timestamp,
    parse_expiration_date,
    source_interim_price,
)
from alphavar.options.lib.normalization.datetime_conversion import df_columns_to_timestamp

_FIXED_TS = pd.Timestamp("2025-04-21T00:00:00", tz=datetime.UTC)


# --- Oracle: the verbatim pre-T20 row-wise enrichment + normalize body ---------------------


def _kind_enrichment_oracle(row: pd.Series) -> pd.Series:
    exch_symbol_arr = DOT_STRIKE_REGEXP.sub(r"\1.\2", row[OptionsTerm.EXCH_SYMBOL]).split("-")
    asset_code = exch_symbol_arr[0]
    row = row.copy(deep=True)
    match len(exch_symbol_arr):
        case 1:
            row[OptionsTerm.ASSET_CODE] = asset_code
            row[OptionsTerm.INSTRUMENT_KIND] = DeribitAssetKind.SPOT.code
            return row
        case 2:
            row[OptionsTerm.ASSET_CODE] = asset_code
            expiration_date = parse_expiration_date(exch_symbol_arr[1])
            if expiration_date is None and exch_symbol_arr[1] != "PERPETUAL":
                raise InstrumentParseError(f"Can not parse {exch_symbol_arr[1]}")
            row[OptionsTerm.EXPIRATION_DATE] = expiration_date
            row[OptionsTerm.INSTRUMENT_KIND] = DeribitAssetKind.FUTURE.code
            return row
        case 3:
            row[OptionsTerm.ASSET_CODE] = asset_code
            row[OptionsTerm.EXPIRATION_DATE] = parse_expiration_date(exch_symbol_arr[2].split("_")[0])
            row[OptionsTerm.INSTRUMENT_KIND] = DeribitAssetKind.FUTURE_COMBO.code
            return row
        case 4:
            row[OptionsTerm.ASSET_CODE] = asset_code
            expiration_date = parse_expiration_date(exch_symbol_arr[1])
            if expiration_date is None:
                expiration_date = parse_expiration_date(exch_symbol_arr[2])
                kind = DeribitAssetKind.OPTION_COMBO.code
                option_type = None
                strike = None
                future_expiration_date = None
            else:
                kind = DeribitAssetKind.OPTION.code
                option_type = exch_symbol_arr[3]
                if option_type not in ["C", "P"]:
                    raise InstrumentParseError(f"Unknown option type {option_type}")
                option_type = OptionsType.CALL.code if exch_symbol_arr[3] == "C" else OptionsType.PUT.code
                strike = float(exch_symbol_arr[2])
                under_arr = row[OptionsTerm.UNDERLYING_CODE].split("-")
                if len(under_arr) == 2:
                    future_expiration_date = parse_expiration_date(under_arr[1])
                else:
                    if row[OptionsTerm.UNDERLYING_CODE] in ["SYN.EXPIRY", "index_price"]:
                        future_expiration_date = None
                    else:
                        raise InstrumentParseError("Can not get expiration from underlying_index")
            row[OptionsTerm.OPTION_RIGHT] = option_type
            row[OptionsTerm.STRIKE] = strike
            row[OptionsTerm.EXPIRATION_DATE] = expiration_date
            row[OptionsTerm.INSTRUMENT_KIND] = kind
            row[OptionsTerm.UNDERLYING_EXPIRATION_DATE] = future_expiration_date
            if (
                row["base_currency"] == row["quote_currency"]
                and "estimated_delivery_price" in row
                and row["estimated_delivery_price"]
            ):
                for col in COLUMNS_TO_CURRENCY:
                    if col in row:
                        row[f"{col}{AbstractExchange.RAW_SUFFIX}"] = row[col]
                        if row[col]:
                            row[col] *= row["estimated_delivery_price"]
                if (
                    OptionsTerm.VOLUME_NOTIONAL in row
                    and "volume_usd" in row
                    and pd.isna(row[OptionsTerm.VOLUME_NOTIONAL])
                ):
                    row[OptionsTerm.VOLUME_NOTIONAL] = row["volume_usd"]
            return row
        case _:
            raise InstrumentParseError(f"Can parse instrument_name {row[OptionsTerm.EXCH_SYMBOL]}")


def _normalize_book_oracle(book_summary_df: pd.DataFrame, request_timestamp: pd.Timestamp) -> pd.DataFrame:
    if book_summary_df.empty:
        return book_summary_df
    book_summary_df[OptionsTerm.REQUEST_TIMESTAMP] = request_timestamp
    rename_columns = {
        "creation_timestamp": OptionsTerm.EXCH_TIMESTAMP,
        "instrument_name": OptionsTerm.EXCH_SYMBOL,
        "underlying_index": OptionsTerm.UNDERLYING_CODE,
        "underlying_price": OptionsTerm.UNDERLYING_PRICE,
        "mark_price": OptionsTerm.EXCH_MARK_PRICE,
        "mark_iv": OptionsTerm.EXCH_MARK_IV,
        "ask_price": OptionsTerm.ASK,
        "bid_price": OptionsTerm.BID,
        "last": OptionsTerm.LAST,
        "high": OptionsTerm.HIGH_24,
        "low": OptionsTerm.LOW_24,
    }
    book_summary_df.rename(columns=rename_columns, inplace=True)
    book_summary_df = df_columns_to_timestamp(book_summary_df, columns=[OptionsTerm.EXCH_TIMESTAMP], unit="ms")
    book_summary_df[OptionsTerm.TIMESTAMP] = book_summary_df[OptionsTerm.EXCH_TIMESTAMP].copy()
    book_summary_df = normalize_timestamp(book_summary_df, columns=[OptionsTerm.TIMESTAMP], freq="1s")
    book_summary_df = fill_option_price(book_summary_df)
    book_summary_df = book_summary_df.apply(_kind_enrichment_oracle, axis="columns", result_type="expand")
    book_summary_df = source_interim_price(book_summary_df)
    return book_summary_df


# --- The test -------------------------------------------------------------------------------


def _canon_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Unify null-likes in object columns (old code leaves Python ``None`` for unset fields,
    the vectorized code leaves ``NaN``) so the comparison is about values, not null spelling."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].where(df[col].notna(), None)
    return df


def _raw_book(deribit_market, kind: DeribitAssetKind | None) -> pd.DataFrame:
    """Raw (pre-normalize) BTC book from the recorded fixture, optionally filtered by kind."""
    params = {"currency": DeribitExchange.CURRENCIES[0]}
    if kind is not None:
        params["kind"] = kind.value
    response = deribit_market.client.request_api("/public/get_book_summary_by_currency", params=params)
    return pd.DataFrame(response["result"])


# None = the full combined book (option/option_combo/future_combo mix); the per-kind books also
# exercise the plain-future and spot branches that the combined fixture happens not to carry.
@pytest.mark.parametrize(
    "kind",
    [None, DeribitAssetKind.FUTURE, DeribitAssetKind.FUTURE_COMBO, DeribitAssetKind.OPTION, DeribitAssetKind.SPOT],
    ids=["combined", "future", "future_combo", "option", "spot"],
)
def test_normalize_book_matches_rowwise_oracle(deribit_market, kind):
    """Vectorized `_normalize_book` == the pre-T20 row-wise oracle on each recorded book."""
    expected = _normalize_book_oracle(_raw_book(deribit_market, kind), _FIXED_TS)
    got = deribit_market._normalize_book(_raw_book(deribit_market, kind), _FIXED_TS)

    assert not got.empty
    pd.testing.assert_frame_equal(
        _canon_nulls(got.reset_index(drop=True)),
        _canon_nulls(expected.reset_index(drop=True)),
        check_like=True,  # ignore incidental column order
        check_dtype=False,  # vectorization yields cleaner dtypes; values are what matter
    )
