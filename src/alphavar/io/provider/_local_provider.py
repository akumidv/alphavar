"""
Local provider
Data should be organized like EXCHANGE_CODE/EXCHANGE_SYMBOL/TRADE_TYPE/TIMEFRAME_CODE/YEAR.parquet
Example: LME/WTI/option/EOD/2024.year
TRADE_TYPE can be: option, future, asset (asset - mean tangible assets: currency, stock, crypto)

dataframe columns:
"""

import datetime
import logging
import os

import pandas as pd
from pydantic import validate_call

from alphavar.core.dictionary import InstrumentKind
from alphavar.io.provider._file_provider import AbstractFileProvider
from alphavar.io.provider._provider_entities import RequestParameters
from alphavar.options.dictionary import OptionsTerm, Timeframe
from alphavar.options.migration import rename_legacy_option_columns as rename_legacy_columns

logger = logging.getLogger(__name__)

# Owner-agreed period semantics (T19, 4VERIFY — see TASKS T19 / D2 ledger):
# A request is always an inclusive range; an open bound resolves to the stored data edge.
#   * ``period_from`` open -> the earliest stored year; set -> that point (inclusive floor).
#   * ``period_to``   open -> the latest stored year;   set -> that point (inclusive ceiling).
# So ``period_to`` alone means "everything up to and including it"; ``period_from`` alone means
# "from it through the latest data"; neither means all stored data.
# A ``date`` bound covers the whole day; a ``datetime`` bound is the exact instant (rows with
# ``timestamp <= to`` / ``>= from``). A year file absent inside the resolved span is skipped
# with a warning.

_Bound = int | datetime.date | datetime.datetime


def _bound_year(bound: _Bound) -> int:
    """Calendar year a from/to bound falls in (``datetime`` is a ``date`` subclass)."""
    if isinstance(bound, bool):  # bool ⊂ int — never a valid period bound
        raise TypeError(f"period bound has incorrect type {type(bound)}")
    if isinstance(bound, int):
        return bound
    if isinstance(bound, datetime.date):  # covers datetime.datetime
        return bound.year
    raise TypeError(f"period bound has incorrect type {type(bound)}")


def _align_ts(series: pd.Series, dt: datetime.datetime) -> pd.Timestamp:
    """Match a naive/aware ``datetime`` bound to the tz of the stored timestamp column."""
    ts = pd.Timestamp(dt)
    col_tz = series.dt.tz
    if col_tz is not None and ts.tz is None:
        return ts.tz_localize(col_tz)
    if col_tz is None and ts.tz is not None:
        return ts.tz_convert(None)
    return ts


def _filter_lower(df: pd.DataFrame, ts_col: str, bound: _Bound | None) -> pd.DataFrame:
    """Keep rows at/after ``bound`` (whole-day floor for ``date``, exact for ``datetime``)."""
    if bound is None or not isinstance(bound, datetime.date):  # None / int year -> no row floor
        return df
    if isinstance(bound, datetime.datetime):
        return df[df[ts_col] >= _align_ts(df[ts_col], bound)]
    return df[df[ts_col].dt.date >= bound]


def _filter_upper(df: pd.DataFrame, ts_col: str, bound: _Bound | None) -> pd.DataFrame:
    """Keep rows at/before ``bound`` (whole-day ceiling for ``date``, exact for ``datetime``)."""
    if bound is None or not isinstance(bound, datetime.date):  # None / int year -> no row ceiling
        return df
    if isinstance(bound, datetime.datetime):
        return df[df[ts_col] <= _align_ts(df[ts_col], bound)]
    return df[df[ts_col].dt.date <= bound]


class PandasLocalFileProvider(AbstractFileProvider):
    """Load data from files by Pandas"""

    def _fn_path_prepare(self, asset_code: str, asset_kind: InstrumentKind, timeframe: Timeframe, year: int):
        return super().fn_path_prepare(asset_code, asset_kind, timeframe, year)

    def _read_years(
        self, asset_kind: InstrumentKind, asset_code: str, timeframe: Timeframe, years: list[int], columns: list | None
    ) -> pd.DataFrame:
        """Concatenate the existing year files in ``years``; a missing year is skipped + warned."""
        frames: list[pd.DataFrame] = []
        for year in years:
            fn_path = self._fn_path_prepare(asset_code, asset_kind, timeframe, year)
            if not os.path.exists(fn_path):
                logger.warning("No %s history for %s %d (%s); skipping", asset_kind.value, asset_code, year, fn_path)
                continue
            frames.append(rename_legacy_columns(pd.read_parquet(fn_path, columns=columns)))
        if not frames:
            return pd.DataFrame(columns=list(columns) if columns else None)
        return pd.concat(frames, ignore_index=True)

    def _load_data_for_period(
        self,
        asset_kind: InstrumentKind,
        asset_code: str,
        params: RequestParameters,
        columns: list,
    ) -> pd.DataFrame:
        period_from, period_to, timeframe = params.period_from, params.period_to, params.timeframe
        ts_col = OptionsTerm.TIMESTAMP

        # An open bound resolves to the stored data edge; the request is always an inclusive range.
        stored = sorted(self.get_asset_history_years(asset_code, asset_kind, timeframe))
        if not stored:
            return pd.DataFrame(columns=list(columns) if columns else None)
        from_year = _bound_year(period_from) if period_from is not None else stored[0]
        to_year = _bound_year(period_to) if period_to is not None else stored[-1]

        years = list(range(min(from_year, to_year), max(from_year, to_year) + 1))
        df_hist = self._read_years(asset_kind, asset_code, timeframe, years, columns)
        df_hist = _filter_lower(df_hist, ts_col, period_from)
        df_hist = _filter_upper(df_hist, ts_col, period_to)
        return df_hist.reset_index(drop=True)

    @validate_call
    def load_options_history(
        self,
        asset_code: str,
        params: RequestParameters | None = None,
        columns: list | None = None,
    ) -> pd.DataFrame:
        """Load option by period, timeframe"""
        if params is None:
            params = RequestParameters()
        if columns is None:
            columns = self.options_columns
        df_hist = self._load_data_for_period(
            asset_kind=InstrumentKind.OPTION,
            asset_code=asset_code,
            params=params,
            columns=columns,
        )
        return df_hist

    def load_options_book(
        self,
        asset_code: str,
        settlement_datetime: datetime.datetime | None = None,
        timeframe: Timeframe = Timeframe.EOD,
        columns: list | None = None,
    ) -> pd.DataFrame:
        """Provide options for datetime, timeframe"""
        raise NotImplementedError

    @validate_call
    def load_futures_history(
        self,
        asset_code: str,
        params: RequestParameters | None = None,
        columns: list | None = None,
    ) -> pd.DataFrame:
        """Load futures data for asset code"""
        if params is None:
            params = RequestParameters()
        if columns is None:
            columns = self.futures_columns
        df_fut = self._load_data_for_period(
            asset_kind=InstrumentKind.FUTURE,
            asset_code=asset_code,
            params=params,
            columns=columns,
        )
        return df_fut

    @validate_call
    def load_futures_book(
        self,
        asset_code: str,
        settlement_datetime: datetime.datetime | None = None,
        timeframe: Timeframe = Timeframe.EOD,
        columns: list | None = None,
    ) -> pd.DataFrame:
        """Provide futures for datetime, timeframe"""
        raise NotImplementedError

    @validate_call
    def load_options_chain(
        self,
        asset_code: str,
        settlement_datetime: datetime.datetime | None = None,
        expiration_date: datetime.datetime | None = None,
        timeframe: Timeframe = Timeframe.EOD,
        columns: list | None = None,
    ) -> pd.DataFrame | None:
        """Local files store only the raw time series, never a pre-selected chain. Return ``None``
        so the facade (``OptionsChain.select_chain``) builds the chain from loaded history. A
        provider backed by a live exchange API may instead return the chain directly."""
        return None
