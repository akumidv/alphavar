"""Timeframe conversion"""

import pandas as pd

from alphavar.options.dictionary import OptionsTerm, Timeframe

# Per-column resample aggregation (engine-specific concern, kept next to the resampler:
# T23.3). Columns absent here (e.g. low_24/high_24) are not aggregated.
# 4VERIFY (owner, D2): reproduces the prior per-column resample_func 1:1.
DEFAULT_RESAMPLE_MODEL: dict[str, str] = {
    OptionsTerm.TIMESTAMP: "last",
    OptionsTerm.STRIKE: "last",
    OptionsTerm.EXPIRATION_DATE: "last",
    OptionsTerm.OPTION_RIGHT: "last",
    OptionsTerm.PRICE: "last",
    OptionsTerm.ASK: "last",
    OptionsTerm.BID: "last",
    OptionsTerm.OPEN_INTEREST: "last",
    OptionsTerm.VOLUME: "last",
    OptionsTerm.VOLUME_PREMIUM: "last",
    OptionsTerm.VOLUME_NOTIONAL: "last",
    OptionsTerm.UNDERLYING_EXPIRATION_DATE: "last",
    OptionsTerm.EXCH_MARK_PRICE: "last",
    OptionsTerm.EXCH_MARK_IV: "last",
    OptionsTerm.OPEN: "first",
    OptionsTerm.CLOSE: "last",
    OptionsTerm.HIGH: "max",
    OptionsTerm.LOW: "min",
    OptionsTerm.REQUEST_TIMESTAMP: "last",
    OptionsTerm.EXCH_TIMESTAMP: "last",
    OptionsTerm.LAST: "last",
    OptionsTerm.UNDERLYING_PRICE: "last",
    OptionsTerm.INTRINSIC_VALUE: "last",
    OptionsTerm.TIMED_VALUE: "last",
    OptionsTerm.PRICE_STATUS: "last",
    OptionsTerm.IV: "mean",
    OptionsTerm.DELTA: "mean",
    OptionsTerm.GAMMA: "mean",
    OptionsTerm.VEGA: "mean",
    OptionsTerm.THETA: "mean",
    OptionsTerm.RHO: "mean",
    OptionsTerm.SERIES_CODE: "last",
    OptionsTerm.ASSET_CODE: "last",
    OptionsTerm.EXCH_SYMBOL: "last",
    OptionsTerm.INSTRUMENT_KIND: "last",
    OptionsTerm.UNDERLYING_CODE: "last",
    OptionsTerm.UNDERLYING_ASSET_CLASS: "last",
    OptionsTerm.BASE_CODE: "last",
    OptionsTerm.TITLE: "last",
    OptionsTerm.OPTION_STYLE: "last",
    OptionsTerm.CURRENCY: "last",
}
# 4VERIFY (owner, D2): the prior list mixed `.nm` with bare enum members
# (exch_timestamp/request_timestamp never matched, a latent bug); now all are real column
# names, so deterministic multi-key sort includes all three timestamps.
RESAMPLE_SORT_COLUMNS = [OptionsTerm.TIMESTAMP, OptionsTerm.EXCH_TIMESTAMP, OptionsTerm.REQUEST_TIMESTAMP]


def convert_to_timeframe(
    df: pd.DataFrame,
    timeframe: Timeframe,
    by_exch_symbol: bool = True,
    resample_model: dict[str, str] | None = None,
):
    """Convert to upper timeframe"""
    if resample_model is None:
        resample_model = DEFAULT_RESAMPLE_MODEL
    columns = list(set([OptionsTerm.TIMESTAMP] + [col for col in resample_model if col in df.columns]))
    sort_columns = [col for col in RESAMPLE_SORT_COLUMNS if col in columns]
    df = df[columns].sort_values(by=sort_columns)
    resample_model = {col: action for col, action in resample_model.items() if col in columns}
    df = _resample_by_kind_type_or_exch_symbol(
        df,
        timeframe=timeframe,
        by_exch_symbol=by_exch_symbol,
        resample_model=resample_model,
        group_columns=None,
    )
    if OptionsTerm.TIMESTAMP in df.columns:
        df.drop(columns=[OptionsTerm.TIMESTAMP], inplace=True)
    df.reset_index(drop=False, inplace=True)
    return df


def _get_group_columns_by_type(df: pd.DataFrame):
    """Prepare list of columns by dataframe content"""
    is_spot = OptionsTerm.EXPIRATION_DATE not in df.columns or df[OptionsTerm.EXPIRATION_DATE].isnull().all()
    is_future = (
        not is_spot
        and df[OptionsTerm.EXPIRATION_DATE].notnull().all()
        and (OptionsTerm.STRIKE not in df.columns or df[OptionsTerm.STRIKE].isnull().all())
    )
    is_option = (
        not is_future
        and OptionsTerm.STRIKE in df.columns
        and OptionsTerm.OPTION_RIGHT in df.columns
        and df[[OptionsTerm.STRIKE, OptionsTerm.OPTION_RIGHT]].notnull().all().all()
    )
    if is_spot:
        group_columns = []
    elif is_future:  # Futures
        group_columns = [OptionsTerm.EXPIRATION_DATE]
    elif is_option:  # Options
        group_columns = [OptionsTerm.EXPIRATION_DATE, OptionsTerm.OPTION_RIGHT, OptionsTerm.STRIKE]
    else:
        raise ValueError(f"Cannot detect type of dataframe by columns and values, try to use {OptionsTerm.ASSET_CODE}")
    if OptionsTerm.ASSET_CODE in df.columns and len(df[OptionsTerm.ASSET_CODE].unique()) > 1:
        group_columns = [OptionsTerm.ASSET_CODE] + group_columns
    return group_columns


def _resample_by_kind_type_or_exch_symbol(
    df: pd.DataFrame,
    timeframe: Timeframe,
    resample_model: dict[str, str],
    by_exch_symbol: bool = True,
    group_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Resample by detection type of asset by column"""
    if group_columns is None:
        if by_exch_symbol:
            # exchange symbol is uniq for each of futures or option contract and should be single for spot
            group_columns = [OptionsTerm.EXCH_SYMBOL]
        else:
            group_columns = _get_group_columns_by_type(df)
        return _resample_by_kind_type_or_exch_symbol(
            df,
            timeframe=timeframe,
            resample_model=resample_model,
            group_columns=group_columns,
            by_exch_symbol=by_exch_symbol,
        )

    if len(group_columns) > 0:
        group = df.groupby(group_columns[0], group_keys=False)
        return group.apply(
            _resample_by_kind_type_or_exch_symbol,
            timeframe=timeframe,
            by_exch_symbol=by_exch_symbol,
            group_columns=group_columns[1:],
            resample_model=resample_model,
        )
    if OptionsTerm.ASSET_CODE in df.columns and len(df[OptionsTerm.ASSET_CODE].unique()) != 1:
        raise ValueError(
            f"Resampled dataframe contain more then one exchange symbol {df[OptionsTerm.ASSET_CODE].unique()}"
        )

    # Carry contract values across gaps before bucketing so an all-NaN target bucket inherits the
    # last known "last" value (LOCF) / the next known "first" value (NOCB), rather than staying
    # NaN. Runs per leaf group (a single contract), so values never leak across contracts. (T24:
    # the prior `df[cols]...ffill(inplace=True)` mutated a throwaway column slice — a no-op.)
    forward_fill_columns = [col for col in resample_model if resample_model[col] == "last" and col in df.columns]
    if forward_fill_columns:
        df[forward_fill_columns] = df[forward_fill_columns].infer_objects(copy=False).ffill()
    back_fill_columns = [col for col in resample_model if resample_model[col] == "first" and col in df.columns]
    if back_fill_columns:
        df[back_fill_columns] = df[back_fill_columns].infer_objects(copy=False).bfill()
    df_resample = df.resample(
        rule=timeframe.offset, on=OptionsTerm.TIMESTAMP, closed="left", label="left", group_keys=False
    ).apply(resample_model)
    return df_resample
