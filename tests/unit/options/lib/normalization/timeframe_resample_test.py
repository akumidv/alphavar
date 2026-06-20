"""Test module for timeframe conversion function"""

import pandas as pd
import pytest

from alphavar.options.dictionary import OptionsTerm, OptionsType, Timeframe
from alphavar.options.lib.normalization.timeframe_resample import _get_group_columns_by_type, convert_to_timeframe


def test__get_group_columns_by_type_spot():
    df = pd.DataFrame({OptionsTerm.PRICE: [123]})
    group_columns = _get_group_columns_by_type(df)
    assert group_columns == []
    df = pd.DataFrame({OptionsTerm.PRICE: [123], OptionsTerm.EXPIRATION_DATE: [pd.NA]})
    group_columns = _get_group_columns_by_type(df)
    assert group_columns == []
    df = pd.DataFrame({OptionsTerm.PRICE: [123, 234], OptionsTerm.ASSET_CODE: ["BTC", "ETH"]})
    group_columns = _get_group_columns_by_type(df)
    assert group_columns == [OptionsTerm.ASSET_CODE]


def test__get_group_columns_by_type_future():
    fut_dict = {OptionsTerm.PRICE: [123, 234], OptionsTerm.EXPIRATION_DATE: [pd.Timestamp.now(), pd.Timestamp.now()]}
    df = pd.DataFrame(fut_dict)
    group_columns = _get_group_columns_by_type(df)
    assert group_columns == [OptionsTerm.EXPIRATION_DATE]
    fut_dict.update({OptionsTerm.STRIKE: [pd.NA, None]})
    df = pd.DataFrame.from_dict(fut_dict)
    group_columns = _get_group_columns_by_type(df)
    assert group_columns == [OptionsTerm.EXPIRATION_DATE]
    fut_dict.update({OptionsTerm.ASSET_CODE: ["BTC", "ETH"]})
    df = pd.DataFrame(fut_dict)
    group_columns = _get_group_columns_by_type(df)
    assert group_columns == [OptionsTerm.ASSET_CODE, OptionsTerm.EXPIRATION_DATE]


def test__get_group_columns_by_type_option():
    opt_dict = {
        OptionsTerm.PRICE: [123, 234],
        OptionsTerm.EXPIRATION_DATE: [pd.Timestamp.now(), pd.Timestamp.now()],
        OptionsTerm.OPTION_RIGHT: [OptionsType.CALL.value, OptionsType.PUT.value],
        OptionsTerm.STRIKE: [1000, 1200],
    }
    df = pd.DataFrame(opt_dict)
    group_columns = _get_group_columns_by_type(df)
    assert group_columns == [OptionsTerm.EXPIRATION_DATE, OptionsTerm.OPTION_RIGHT, OptionsTerm.STRIKE]
    opt_dict.update({OptionsTerm.ASSET_CODE: ["BTC", "ETH"]})
    df = pd.DataFrame(opt_dict)
    group_columns = _get_group_columns_by_type(df)
    assert group_columns == [
        OptionsTerm.ASSET_CODE,
        OptionsTerm.EXPIRATION_DATE,
        OptionsTerm.OPTION_RIGHT,
        OptionsTerm.STRIKE,
    ]


def test__get_group_columns_by_type_wrong_option():
    opt_dict = {
        OptionsTerm.PRICE: [123, 234],
        OptionsTerm.EXPIRATION_DATE: [pd.Timestamp.now(), pd.Timestamp.now()],
        OptionsTerm.OPTION_RIGHT: [OptionsType.CALL.value, pd.NA],
        OptionsTerm.STRIKE: [1000, 1200],
    }
    df = pd.DataFrame(opt_dict)
    with pytest.raises(ValueError):
        _ = _get_group_columns_by_type(df)
    opt_dict = {
        OptionsTerm.PRICE: [123, 234],
        OptionsTerm.EXPIRATION_DATE: [pd.Timestamp.now(), pd.Timestamp.now()],
        OptionsTerm.OPTION_RIGHT: [OptionsType.CALL.value, OptionsType.PUT.value],
        OptionsTerm.STRIKE: [1000, None],
    }
    df = pd.DataFrame(opt_dict)
    with pytest.raises(ValueError):
        _ = _get_group_columns_by_type(df)


def test_convert_to_timeframe_future(future_update_files):
    dfs = []
    for fn in future_update_files[:5]:
        dfs.append(pd.read_parquet(fn))
    df = pd.concat(dfs)
    df_new_tf = convert_to_timeframe(df, Timeframe.EOD)
    assert len(df_new_tf) != len(df)
    assert len(df_new_tf[OptionsTerm.EXPIRATION_DATE].unique()) == len(df[OptionsTerm.EXPIRATION_DATE].unique())
    assert len(df_new_tf[OptionsTerm.ASSET_CODE].unique()) == len(df[OptionsTerm.ASSET_CODE].unique())


def test_convert_to_timeframe_option(option_update_files):
    dfs = []
    for fn in option_update_files[:5]:
        dfs.append(pd.read_parquet(fn))
    df = pd.concat(dfs, ignore_index=True)
    df_new_tf = convert_to_timeframe(df, Timeframe.EOD)
    assert len(df_new_tf) != len(df)
    assert len(df_new_tf[OptionsTerm.EXPIRATION_DATE].unique()) == len(df[OptionsTerm.EXPIRATION_DATE].unique())
    assert len(df_new_tf[OptionsTerm.ASSET_CODE].unique()) == len(df[OptionsTerm.ASSET_CODE].unique())


def test_convert_to_timeframe_option_by_type(option_update_files):
    dfs = []
    for fn in option_update_files[:5]:
        dfs.append(pd.read_parquet(fn))
    df = pd.concat(dfs)
    df_new_tf = convert_to_timeframe(df, Timeframe.EOD, by_exch_symbol=False)
    assert len(df_new_tf) != len(df)
    assert len(df_new_tf[OptionsTerm.EXPIRATION_DATE].unique()) == len(df[OptionsTerm.EXPIRATION_DATE].unique())
    assert len(df_new_tf[OptionsTerm.ASSET_CODE].unique()) == len(df[OptionsTerm.ASSET_CODE].unique())


def test_convert_to_timeframe_fills_gap_buckets():
    """A target bucket whose rows are all-NaN for a column inherits the last known `last` value
    (LOCF) and the next known `first` value (NOCB), per contract — the gap pre-fill is real, not
    a no-op (T24). Single contract resampled 30m: the 00:30 bucket's source rows carry NaN
    price/open but must resolve to the carried values, not NaN."""
    ts = pd.to_datetime(
        ["2025-01-01 00:00", "2025-01-01 00:15", "2025-01-01 00:35", "2025-01-01 00:50", "2025-01-01 01:00"],
        utc=True,
    )
    df = pd.DataFrame(
        {
            OptionsTerm.TIMESTAMP: ts,
            OptionsTerm.EXCH_SYMBOL: ["BTC-TEST"] * 5,
            OptionsTerm.STRIKE: [100.0] * 5,
            OptionsTerm.PRICE: [10.0, 11.0, None, None, 13.0],  # "last"
            OptionsTerm.OPEN: [10.0, 11.0, None, None, 13.0],  # "first"
        }
    )
    out = convert_to_timeframe(df, Timeframe.MINUTE_30).set_index(OptionsTerm.TIMESTAMP)
    gap = pd.Timestamp("2025-01-01 00:30", tz="UTC")
    assert out.loc[gap, OptionsTerm.PRICE] == 11.0  # LOCF: last known price carried forward
    assert out.loc[gap, OptionsTerm.OPEN] == 13.0  # NOCB: next known open carried back
    assert out.loc[gap, OptionsTerm.STRIKE] == 100.0  # contract identity intact
