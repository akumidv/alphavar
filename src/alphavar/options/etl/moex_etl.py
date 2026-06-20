"""MOEX ETL module"""

import datetime

import pandas as pd

from alphavar.core.dictionary import InstrumentKind
from alphavar.io.exchange import MoexExchange
from alphavar.io.exchange.moex import MoexAssetType
from alphavar.io.messanger import AbstractMessanger
from alphavar.options.dictionary import (
    OptionsTerm,
    Timeframe,
)
from alphavar.options.etl.etl_class import AssetBookData, EtlOptions, SaveTask, validate_book_data


class EtlMoex(EtlOptions):
    """Deribit ETL process
    Updates in store size for timeframes (2025 year, x5 in memory)
    1m timeframe ~750Mb a day, 22.5 Gb a month 275 Gb a year in store
    5m timeframe ~ 150Mb a day, 4.5Gb a month, 60Gb a year
    1h timeframe ~ 11.5Mb a day, 350Mb a month, 4.5Gb a year
    """

    def __init__(
        self,
        exchange: MoexExchange,
        asset_names: list[str] | str | None,
        timeframe: Timeframe,
        update_data_path: str,
        timeframe_cron: dict | str | None = None,
        messanger: AbstractMessanger | None = None,
        is_detailed: bool = False,
    ):
        super().__init__(exchange, asset_names, timeframe, update_data_path, timeframe_cron, messanger, is_detailed)

    @staticmethod
    def _drop_service_or_doublet_columns(df: pd.DataFrame) -> pd.DataFrame:
        drop_columns = []
        for col in df.columns:
            if col.endswith(MoexExchange.RAW_SUFFIX) and df[col].isnull().all():
                drop_columns.append(col)
        if len(drop_columns) > 0:
            df.drop(columns=drop_columns, inplace=True)
        return df

    def get_symbols_books_snapshot(
        self, asset_name: list[str] | str | None, request_timestamp: pd.Timestamp | None = None
    ) -> AssetBookData:
        """Load deribit option and future"""
        if request_timestamp is None:
            request_timestamp = pd.Timestamp.now(tz=datetime.UTC)
        book_summary_df = self.exchange.get_options_assets_books_snapshot(asset_name)
        if book_summary_df is None or book_summary_df.empty:
            return AssetBookData(
                asset_name=asset_name,
                request_timestamp=request_timestamp,
                options=None,
                futures=None,
                spot=None,
            )
        book_summary_df[OptionsTerm.REQUEST_TIMESTAMP] = request_timestamp
        options_df = book_summary_df[
            book_summary_df[OptionsTerm.INSTRUMENT_KIND] == InstrumentKind.OPTION.value
        ].reset_index(drop=True)
        future_columns = [
            OptionsTerm.TIMESTAMP,
            OptionsTerm.ASSET_CODE,
            OptionsTerm.UNDERLYING_CODE,
            OptionsTerm.UNDERLYING_ASSET_CLASS,
            OptionsTerm.UNDERLYING_EXPIRATION_DATE,
            OptionsTerm.UNDERLYING_PRICE,
        ]
        futures_mask = book_summary_df[OptionsTerm.UNDERLYING_ASSET_CLASS] == MoexAssetType.FUTURES.code
        future_df = (
            book_summary_df[futures_mask][future_columns]
            .drop_duplicates(subset=[OptionsTerm.UNDERLYING_CODE])
            .rename(
                columns={
                    OptionsTerm.UNDERLYING_CODE: OptionsTerm.ASSET_CODE,
                    OptionsTerm.UNDERLYING_ASSET_CLASS: OptionsTerm.INSTRUMENT_KIND,
                    OptionsTerm.UNDERLYING_EXPIRATION_DATE: OptionsTerm.EXPIRATION_DATE,
                    OptionsTerm.UNDERLYING_PRICE: OptionsTerm.PRICE,
                }
            )
        )
        future_df = self._drop_service_or_doublet_columns(future_df)
        spot_columns = [
            OptionsTerm.TIMESTAMP,
            OptionsTerm.UNDERLYING_CODE,
            OptionsTerm.UNDERLYING_ASSET_CLASS,
            OptionsTerm.UNDERLYING_PRICE,
        ]
        spot_df = (
            book_summary_df[~futures_mask][spot_columns]
            .drop_duplicates(subset=[OptionsTerm.UNDERLYING_CODE, OptionsTerm.UNDERLYING_ASSET_CLASS])
            .rename(
                columns={
                    OptionsTerm.UNDERLYING_CODE: OptionsTerm.ASSET_CODE,
                    OptionsTerm.UNDERLYING_ASSET_CLASS: OptionsTerm.INSTRUMENT_KIND,
                    OptionsTerm.UNDERLYING_PRICE: OptionsTerm.PRICE,
                }
            )
        )
        spot_df = self._drop_service_or_doublet_columns(spot_df)

        return validate_book_data(
            AssetBookData(
                asset_name=asset_name,
                request_timestamp=request_timestamp,
                options=options_df if not options_df.empty else None,
                futures=future_df if not future_df.empty else None,
                spot=spot_df if not spot_df.empty else None,
            )
        )

    def _add_save_task_to_background_to_asset_name(
        self, df: pd.DataFrame, asset_kind: InstrumentKind, request_datetime: pd.Timestamp
    ):
        asset_name = df.iloc[0][OptionsTerm.ASSET_CODE]
        save_path = self.get_timeframe_update_path(asset_name, asset_kind, request_datetime)
        self.add_save_task_to_background(SaveTask(save_path, df.copy()))

    def _save_timeframe_book_update(self, book_data: AssetBookData):
        """Save book data"""

        # Save updates under the canonical singular kind token (ADR 0001). MOEX has no
        # venue-specific spelling, so the venue-native token is the canon itself.
        fabric = {
            "options": InstrumentKind.OPTION,
            "futures": InstrumentKind.FUTURE,
            "spot": InstrumentKind.SPOT,
        }
        request_datetime = book_data.request_timestamp
        for asset_kind_attr in fabric:
            df = getattr(book_data, asset_kind_attr)
            if df is not None:
                df.groupby(OptionsTerm.ASSET_CODE, group_keys=False).apply(
                    self._add_save_task_to_background_to_asset_name,
                    asset_kind=fabric[asset_kind_attr],
                    request_datetime=request_datetime,
                    include_groups=True,
                )
                setattr(book_data, asset_kind_attr, None)
