"""
Deribit api provider
"""

import concurrent
import datetime
import logging
import re
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from pydantic import validate_call

from alphavar.core.dictionary import InstrumentKind
from alphavar.io.exchange._abstract_exchange import AbstractExchange, APIException, RequestClass
from alphavar.io.exchange.cache import Cache
from alphavar.io.exchange.exchange_entities import ExchangeCode
from alphavar.io.provider import DataEngine, RequestParameters
from alphavar.options.dictionary import (
    AssetType,
    ContractKind,
    Currency,
    OptionsStyle,
    OptionsTerm,
    OptionsType,
    Timeframe,
)
from alphavar.options.dictionary.enum_code import EnumCode
from alphavar.options.lib.normalization import (
    fill_option_price,
    normalize_timestamp,
    parse_expiration_date,
    source_interim_price,
)
from alphavar.options.lib.normalization.datetime_conversion import df_columns_to_timestamp

logger = logging.getLogger(__name__)


ttl_cache = Cache(128, is_new_day_ttl_reset=True)


class MoexAssetType(EnumCode):
    """https://iss.moex.com/iss/docs/option-calc/v1/glossary/
    sset_type = currency, share, futures, commodity, index
    asset_subtype – for futures: currency, share, commodity, index)"""

    CURRENCY = AssetType.CURRENCY.value, AssetType.CURRENCY.code
    SHARE = AssetType.SHARE.value, AssetType.SHARE.code
    COMMODITY = AssetType.COMMODITY.value, AssetType.COMMODITY.code
    INDEX = AssetType.INDEX.value, AssetType.INDEX.code
    FUTURES = "futures", "f"
    # OPTION = AssetType.OPTION.value, AssetType.OPTION.code


# option_type – (call, put)
# series_type = W – week, M – month, Q – quarter
DOT_STRIKE_REGEXP = re.compile(r"(\d)d(\d)", flags=re.IGNORECASE)
COLUMNS_TO_CURRENCY = [
    OptionsTerm.ASK,
    OptionsTerm.BID,
    OptionsTerm.LAST,
    OptionsTerm.HIGH_24,
    OptionsTerm.LOW_24,
    OptionsTerm.EXCH_MARK_PRICE,
]


class MoexOptions:
    """Moex options calculator api
    https://iss.moex.com/iss/docs/option-calc/v1/about/
    """

    def __init__(self, client: RequestClass):
        self.client = client

    def get_assets(self, asset_type: MoexAssetType | str | None = None) -> pd.DataFrame:
        """Assets list
                https://iss.moex.com/iss/docs/option-calc/v1/requests_option/#_2
                Response example:
                 asset_code           title asset_type underlying_type
        3           AFLT          AFLT (Аэрофлот)      s          None
        4           AFLT           AFLT (фьючерс)      f           s
        8             BR             BR (фьючерс)      f           m
        26          HANG           HANG (фьючерс)      f           i
        28         IMOEX  IMOEX (Индекс МосБиржи)      i          None
        67            SI             Si (фьючерс)     f           c
        86  USD000UTSTOM               USDRUB_TOM     c          None
        """
        params = self._get_asset_type_params(None, asset_type)
        response = self.client.request_api("/assets", params=params)
        # TODO replace asset type and asset_subtype to AssetType code
        asset_codes_df = (
            pd.DataFrame(response)
            .rename(
                columns={"asset_type": OptionsTerm.INSTRUMENT_KIND, "asset_subtype": OptionsTerm.UNDERLYING_ASSET_CLASS}
            )
            .replace(
                {
                    OptionsTerm.INSTRUMENT_KIND: {at.value: at.code for at in MoexAssetType},
                    OptionsTerm.UNDERLYING_ASSET_CLASS: {at.value: at.code for at in MoexAssetType},
                }
            )
        )
        return asset_codes_df

    @staticmethod
    def _get_asset_type_params(params: dict | None = None, asset_type: MoexAssetType | str | None = None):
        if not asset_type:
            return params
        asset_type = asset_type if isinstance(asset_type, MoexAssetType) else MoexAssetType(asset_type)
        asset_type_query = {"asset_type": asset_type.value}
        if params is None:
            params = {}
        params.update(asset_type_query)
        return params

    @validate_call
    def get_asset_info(self, asset_code: str, asset_type: MoexAssetType | str | None = None) -> pd.Series:
        """Asset info
                https://iss.moex.com/iss/docs/option-calc/v1/requests_option/#_3

        asset_code                       SI
        title              Si (фьючерс)
        asset_type                    f
        underlying_type               c
        """
        params = self._get_asset_type_params(None, asset_type)
        response = self.client.request_api(f"/assets/{asset_code}", params=params)
        data = {}
        for key, value in response.items():
            if key == "asset_type":
                key = OptionsTerm.INSTRUMENT_KIND
                value = MoexAssetType(value).code
            elif key == "asset_subtype":
                key = OptionsTerm.UNDERLYING_ASSET_CLASS
                value = MoexAssetType(value).code
            data[key] = value
        asset_data = pd.Series(data)
        return asset_data

    @validate_call
    def get_asset_futures(self, asset_code: str) -> pd.DataFrame:
        """
                https://iss.moex.com/iss/docs/option-calc/v1/requests_option/#_4

                :param asset_code:
                :return:
           asset_code base_asset_code asset_type expiration_date
        0         AFM5       AFLT    f      2025-06-20
        1         AFU5       AFLT    f      2025-09-19
        """
        response = self.client.request_api(f"/assets/{asset_code}/futures")
        fut_df = (
            pd.DataFrame(response)
            .rename(
                columns={
                    "asset_code": OptionsTerm.ASSET_CODE,
                    "futures_code": OptionsTerm.EXCH_SYMBOL,
                    "asset_type": OptionsTerm.INSTRUMENT_KIND,
                }
            )
            .replace({OptionsTerm.INSTRUMENT_KIND: {at.value: at.code for at in MoexAssetType}})
        )
        fut_df = df_columns_to_timestamp(fut_df, columns=[OptionsTerm.EXPIRATION_DATE])
        return fut_df

    @validate_call
    def get_asset_options(self, asset_code: str) -> pd.DataFrame | None:
        """
                https://iss.moex.com/iss/docs/option-calc/v1/requests_option/#_5
        Sample response recorded under tests/unit/io/exchange/fixtures/moex/.
        """
        try:
            response = self.client.request_api(f"/assets/{asset_code}/options")
            opt_df = (
                pd.DataFrame(response)
                .rename(
                    columns={
                        "asset_code": OptionsTerm.ASSET_CODE,
                        "futures_code": OptionsTerm.UNDERLYING_CODE,
                        "asset_type": OptionsTerm.UNDERLYING_ASSET_CLASS,
                        "secid": OptionsTerm.EXCH_SYMBOL,
                    }
                )
                .replace(
                    {
                        OptionsTerm.UNDERLYING_ASSET_CLASS: {at.value: at.code for at in MoexAssetType},
                        OptionsTerm.OPTION_RIGHT: {at.value: at.code for at in OptionsType},
                    }
                )
            )
            opt_df[OptionsTerm.INSTRUMENT_KIND] = InstrumentKind.OPTION.value
            opt_df = df_columns_to_timestamp(opt_df, columns=[OptionsTerm.EXPIRATION_DATE])
            return opt_df
        except APIException as err:
            if err.status_code == 422:
                return None
            raise err from err

    @validate_call
    def calc_options(
        self,
        asset_code: str,
        option_series: str,
        asset_type: MoexAssetType | str | None = None,
    ) -> pd.DataFrame | None:
        """
        https://iss.moex.com/iss/docs/option-calc/v1/requests_option/#_6
        :param asset_code:
        :param option_series:
        :param asset_type:
        :return:
        """
        raise NotImplementedError

    @validate_call
    def get_option_series(self, asset_code: str, asset_type: MoexAssetType | str | None = None) -> pd.DataFrame | None:
        """
                https://iss.moex.com/iss/docs/option-calc/v1/requests_optionboard/#_2
        Sample response recorded under tests/unit/io/exchange/fixtures/moex/.
        """
        try:
            params = self._get_asset_type_params(None, asset_type)
            response = self.client.request_api(f"/assets/{asset_code}/optionseries", params=params)
            options = []
            for series_call in response:
                call = series_call["call"]
                put = series_call["put"]
                del series_call["call"]
                del series_call["put"]
                series_call["updatetime"] = series_call["updatetime"] + "+03:00"
                series_put = series_call.copy()
                series_call[OptionsTerm.OPTION_RIGHT] = OptionsType.CALL.code
                series_put[OptionsTerm.OPTION_RIGHT] = OptionsType.PUT.code
                series_call.update(call)
                series_put.update(put)
                options.extend([series_call, series_put])
            opt_df = (
                pd.DataFrame(options)
                .rename(
                    columns={
                        "asset_code": OptionsTerm.ASSET_CODE,
                        "asset_type": OptionsTerm.UNDERLYING_ASSET_CLASS,
                        "futures_code": OptionsTerm.UNDERLYING_CODE,
                        "optionseries_code": OptionsTerm.SERIES_CODE,
                        "updatetime": OptionsTerm.EXCH_TIMESTAMP,
                        "volume_rub": OptionsTerm.VOLUME_PREMIUM,
                        "volume_contracts": OptionsTerm.VOLUME,
                        "openposition": OptionsTerm.OPEN_INTEREST,
                    }
                )
                .replace({OptionsTerm.UNDERLYING_ASSET_CLASS: {at.value: at.code for at in MoexAssetType}})
            )
            opt_df = df_columns_to_timestamp(opt_df, columns=[OptionsTerm.EXPIRATION_DATE, OptionsTerm.EXCH_TIMESTAMP])
            opt_df[OptionsTerm.INSTRUMENT_KIND] = InstrumentKind.OPTION.value
            return opt_df
        except APIException as err:
            if err.status_code == 422:
                return None
            raise err from err

    def get_option_series_info(
        self, asset_code: str, series_code: str, asset_type: MoexAssetType | str | None = None
    ) -> pd.DataFrame | None:
        """
        https://iss.moex.com/iss/docs/option-calc/v1/requests_optionboard/#_3
        """
        raise NotImplementedError

    @validate_call
    def get_option_series_list(
        self,
        asset_code: str,
        series_code: str,
        asset_type: MoexAssetType | str | None = None,
        strike: int | None = None,
        option_type: OptionsType | None = None,
    ) -> pd.DataFrame | None:
        """
                https://iss.moex.com/iss/docs/option-calc/v1/requests_optionboard/#_4
        Sample response recorded under tests/unit/io/exchange/fixtures/moex/.
        """
        try:
            params = self._get_asset_type_params(None, asset_type)
            response = self.client.request_api(
                f"/assets/{asset_code}/optionseries/{series_code}/options", params=params
            )
            opt_df = (
                pd.DataFrame(response)
                .rename(
                    columns={
                        "asset_code": OptionsTerm.ASSET_CODE,
                        "futures_code": OptionsTerm.UNDERLYING_CODE,
                        "asset_type": OptionsTerm.UNDERLYING_ASSET_CLASS,
                        "secid": OptionsTerm.EXCH_SYMBOL,
                    }
                )
                .replace(
                    {
                        OptionsTerm.UNDERLYING_ASSET_CLASS: {at.value: at.code for at in MoexAssetType},
                        OptionsTerm.OPTION_RIGHT: {at.value: at.code for at in OptionsType},
                    }
                )
            )
            opt_df = df_columns_to_timestamp(opt_df, columns=[OptionsTerm.EXPIRATION_DATE])
            opt_df[OptionsTerm.INSTRUMENT_KIND] = InstrumentKind.OPTION.value
            opt_df[OptionsTerm.SERIES_CODE] = series_code
            return opt_df

        except APIException as err:
            if err.status_code == 422:
                return None
            raise err from err

    @validate_call
    def get_option_series_desk(
        self, asset_code: str, series_code: str, asset_type: MoexAssetType | str | None = None, rows: int | None = None
    ) -> pd.DataFrame | None:
        """
        https://iss.moex.com/iss/docs/option-calc/v1/requests_optionboard/#_5
        Sample response recorded under tests/unit/io/exchange/fixtures/moex/.
        """
        try:
            request_timestamp = pd.Timestamp.now(tz=datetime.UTC)
            params = self._get_asset_type_params(None, asset_type)
            response = self.client.request_api(
                f"/assets/{asset_code}/optionseries/{series_code}/optionboard", params=params
            )
            opt_df = self._normalize_option_desk(response, asset_code, series_code, asset_type, request_timestamp)
            return opt_df
        except APIException as err:
            if err.status_code == 422:
                return None
            raise err from err

    def _normalize_option_desk(
        self,
        response: dict,
        asset_code: str,
        series_code: str,
        asset_type: MoexAssetType | str | None = None,
        request_timestamp: pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        options = []
        for call in response["call"]:
            call[OptionsTerm.OPTION_RIGHT] = OptionsType.CALL.code
            options.append(call)
        for put in response["put"]:
            put[OptionsTerm.OPTION_RIGHT] = OptionsType.PUT.code
            options.append(put)

        opt_df = (
            pd.DataFrame(options)
            .rename(
                columns={
                    "secid": OptionsTerm.EXCH_SYMBOL,
                    "offer": OptionsTerm.ASK,
                    "theorprice": OptionsTerm.EXCH_MARK_PRICE,
                    "volatility": OptionsTerm.EXCH_MARK_IV,
                }
            )
            .replace(
                {
                    OptionsTerm.UNDERLYING_ASSET_CLASS: {at.value: at.code for at in MoexAssetType},
                    OptionsTerm.OPTION_RIGHT: {at.value: at.code for at in OptionsType},
                }
            )
            .sort_values(by=[OptionsTerm.STRIKE, OptionsTerm.OPTION_RIGHT])
            .reset_index(drop=True)
        )
        if asset_type is not None:
            opt_df[OptionsTerm.UNDERLYING_ASSET_CLASS] = (
                asset_type.code if isinstance(asset_type, MoexAssetType) else MoexAssetType(asset_type).code
            )
        opt_df = df_columns_to_timestamp(opt_df, columns=[OptionsTerm.EXPIRATION_DATE])
        opt_df[OptionsTerm.ASSET_CODE] = asset_code
        opt_df[OptionsTerm.INSTRUMENT_KIND] = InstrumentKind.OPTION.value
        opt_df[OptionsTerm.SERIES_CODE] = series_code
        opt_df[OptionsTerm.OPTION_STYLE] = (
            OptionsStyle.AMERICAN.code if series_code.lower().endswith("a") else OptionsStyle.EUROPEAN.code
        )
        opt_df[OptionsTerm.EXPIRATION_DATE] = parse_expiration_date(series_code[-8:-2])
        opt_df[OptionsTerm.REQUEST_TIMESTAMP] = (
            pd.Timestamp.now(tz=datetime.UTC) if request_timestamp is None else request_timestamp
        )
        opt_df[OptionsTerm.TIMESTAMP] = opt_df[OptionsTerm.REQUEST_TIMESTAMP].copy()
        opt_df = normalize_timestamp(opt_df, columns=[OptionsTerm.TIMESTAMP], freq="1s")
        opt_df[OptionsTerm.CURRENCY] = Currency.RUB.code
        # https://www.moex.com/s205

        opt_df = fill_option_price(opt_df)  # -> exch_price (venue traded, RUB)
        opt_df = source_interim_price(opt_df)  # price <- exch_price (interim, T23.6)
        opt_df_call_otm = opt_df[
            (opt_df[OptionsTerm.OPTION_RIGHT] == OptionsType.CALL.code) & (opt_df[OptionsTerm.INTRINSIC_VALUE] > 0)
        ]
        underlying_price = (
            opt_df_call_otm.iloc[0][OptionsTerm.STRIKE] + opt_df_call_otm.iloc[0][OptionsTerm.INTRINSIC_VALUE]
        )
        opt_df[OptionsTerm.UNDERLYING_PRICE] = underlying_price
        return opt_df


class MoexExchange(AbstractExchange):
    """Deribit exchange api"""

    PRODUCT_API_URL: str = "https://iss.moex.com/iss/apps/option-calc/v1"
    TEST_API_URL: str = "https://iss.moex.com/iss/apps/option-calc/v1"
    CURRENCIES = [Currency.RUB.value]
    TASKS_LIMIT: int = 2

    # MOEX stores update snapshots under the canonical singular kind token already (no
    # venue-specific spelling, no combos) — so the mapping is the identity (ADR 0001).
    INSTRUMENT_KIND_MAP: dict[str, tuple[InstrumentKind, ContractKind]] = {
        InstrumentKind.OPTION.value: (InstrumentKind.OPTION, ContractKind.VANILLA),
        InstrumentKind.FUTURE.value: (InstrumentKind.FUTURE, ContractKind.VANILLA),
        InstrumentKind.SPOT.value: (InstrumentKind.SPOT, ContractKind.VANILLA),
    }

    def __init__(self, engine: DataEngine = DataEngine.PANDAS, api_url: str | None = None):
        """Init"""
        api_url = api_url if api_url else self.PRODUCT_API_URL
        super().__init__(engine, ExchangeCode.MOEX.name, api_url=api_url, http_params={"timeout": 30})
        self.options = MoexOptions(self.client)

    @ttl_cache.it
    def _request_asset_options(self, asset_code: str) -> pd.DataFrame | None:
        try:
            return self.options.get_asset_options(asset_code)
        except Exception as err:
            logger.error("asset options request for %s: %s", asset_code, err)
            return None

    def get_asset_history_years(self, asset_code: str, asset_kind: InstrumentKind, timeframe: Timeframe) -> list[int]:
        """Exchange API does not provide per-year history."""
        raise NotImplementedError

    def get_assets_list(self, asset_kind: InstrumentKind | str | None = None) -> list[str]:
        """ """
        asset_codes = self._get_asset_list_wo_options(asset_kind)
        if asset_kind not in [InstrumentKind.OPTION, InstrumentKind.OPTION.value]:
            return asset_codes
        options_asset_codes = []
        with ThreadPoolExecutor(max_workers=self.TASKS_LIMIT) as executor:
            job_results = {
                executor.submit(self._request_asset_options, asset_code): asset_code for asset_code in asset_codes
            }
            for job_res in concurrent.futures.as_completed(job_results):
                opt_df: pd.DataFrame | Exception | None = job_res.result()
                if isinstance(opt_df, pd.DataFrame):
                    asset_code = job_results[job_res]
                    options_asset_codes.append(asset_code)
        return options_asset_codes

    @ttl_cache.it
    def _get_asset_list_wo_options(self, asset_kind: InstrumentKind | str | None = None):
        if asset_kind in [InstrumentKind.OPTION, InstrumentKind.OPTION.value]:
            asset_kind = None
        elif asset_kind in [InstrumentKind.FUTURE, InstrumentKind.FUTURE.value, MoexAssetType.FUTURES.value]:
            asset_kind = MoexAssetType.FUTURES
        elif isinstance(asset_kind, AssetType):
            asset_kind = MoexAssetType(asset_kind.value)  # TODO REFACTOR THIS, due changes in asset type to assend kind
        assets_code_df = self.options.get_assets(asset_kind)
        asset_codes = [asset_code.upper() for asset_code in assets_code_df[OptionsTerm.ASSET_CODE].unique()]
        return asset_codes

    def _request_series(self, asset_code: str):
        try:
            return self.options.get_option_series(asset_code)
        except Exception as err:
            logger.error("option series request for %s: %s", asset_code, err)
            return None

    @ttl_cache.it
    def _get_options_series(self, asset_codes: list[str]) -> pd.DataFrame:
        asset_series = []
        with ThreadPoolExecutor(max_workers=self.TASKS_LIMIT) as executor:
            job_results = {executor.submit(self._request_series, asset_code): asset_code for asset_code in asset_codes}
            for job_res in concurrent.futures.as_completed(job_results):
                series_df: pd.DataFrame | Exception | None = job_res.result()
                if isinstance(series_df, pd.DataFrame):
                    asset_series.append(series_df)
                # else:
                #     raise FileNotFoundError(f'Asset code {asset_code} is not options')
        asset_series_df = pd.concat(asset_series, ignore_index=True) if len(asset_series) > 1 else asset_series[0]
        return asset_series_df

    def _request_underlying(self, asset_code: str):
        try:
            return self.options.get_asset_futures(asset_code)
        except Exception as err:
            logger.error("option underlying request for %s: %s", asset_code, err)
            return None

    @ttl_cache.it
    def _get_underlyings(self, asset_codes: list[str]) -> pd.DataFrame:
        asset_underlying = []
        with ThreadPoolExecutor(max_workers=self.TASKS_LIMIT) as executor:
            job_results = {
                executor.submit(self._request_underlying, asset_code): asset_code for asset_code in asset_codes
            }
            for job_res in concurrent.futures.as_completed(job_results):
                underlying_df: pd.DataFrame | Exception | None = job_res.result()
                if isinstance(underlying_df, pd.DataFrame):
                    asset_underlying.append(underlying_df)
        asset_underlying_df = (
            pd.concat(asset_underlying, ignore_index=True) if len(asset_underlying) > 1 else asset_underlying[0]
        )
        return asset_underlying_df

    def _request_desk(self, asset_code: str, series_code: str):
        try:
            opt_df = self.options.get_option_series_desk(asset_code=asset_code, series_code=series_code)
            return opt_df
        except Exception as err:
            logger.error("get desk for %s %s: %s", asset_code, series_code, err)
            return None

    def get_options_assets_books_snapshot(
        self, asset_codes: list[str] | str | None = None
    ) -> pd.DataFrame:  # TODO rename symbols to assets and in deribit too
        """Get all option snapshot
        Request time: ~2min
        """
        # print('\n[WARNING] for get_options_assets_books_snapshot used STATIC FILE')
        # return pd.read_parquet('./book_summary_df.parquet')
        if asset_codes is None:
            asset_codes = self._get_asset_list_wo_options(InstrumentKind.OPTION)
        elif isinstance(asset_codes, str):
            asset_codes = [asset_codes]
        asset_series_df = self._get_options_series(asset_codes)[
            [
                OptionsTerm.SERIES_CODE,
                OptionsTerm.ASSET_CODE,
                OptionsTerm.UNDERLYING_CODE,
                OptionsTerm.UNDERLYING_ASSET_CLASS,
                OptionsTerm.EXCH_TIMESTAMP,
            ]
        ]
        futures_asset_codes = list(
            asset_series_df[asset_series_df[OptionsTerm.UNDERLYING_ASSET_CLASS] == MoexAssetType.FUTURES.code][
                OptionsTerm.ASSET_CODE
            ].unique()
        )
        futures_asset_underlying_df = self._get_underlyings(futures_asset_codes)[
            [OptionsTerm.EXCH_SYMBOL, OptionsTerm.INSTRUMENT_KIND, OptionsTerm.EXPIRATION_DATE]
        ].rename(
            columns={
                # the underlying future's *contract* code matches the option's UNDERLYING_CODE
                OptionsTerm.EXCH_SYMBOL: OptionsTerm.UNDERLYING_CODE,
                OptionsTerm.INSTRUMENT_KIND: OptionsTerm.UNDERLYING_ASSET_CLASS,
                OptionsTerm.EXPIRATION_DATE: OptionsTerm.UNDERLYING_EXPIRATION_DATE,
            }
        )
        asset_series_df = asset_series_df.merge(
            futures_asset_underlying_df,
            left_on=[OptionsTerm.UNDERLYING_CODE, OptionsTerm.UNDERLYING_ASSET_CLASS],
            right_on=[OptionsTerm.UNDERLYING_CODE, OptionsTerm.UNDERLYING_ASSET_CLASS],
            how="left",
        )
        tasks = [
            [asset_code, series_code]
            for asset_code in asset_series_df[OptionsTerm.ASSET_CODE].unique()
            for series_code in list(
                asset_series_df[asset_series_df[OptionsTerm.ASSET_CODE] == asset_code][OptionsTerm.SERIES_CODE].unique()
            )
        ]
        books = []
        with ThreadPoolExecutor(max_workers=self.TASKS_LIMIT) as executor:
            job_results = {
                executor.submit(self._request_desk, asset_code, series_code): [asset_code, series_code]
                for asset_code, series_code in tasks
            }
            for job_res in concurrent.futures.as_completed(job_results):
                book_summary_df: pd.DataFrame | Exception = job_res.result()
                if isinstance(book_summary_df, pd.DataFrame):
                    books.append(book_summary_df)
                else:
                    asset_code, series_code = job_results[job_res]
                    logger.error("for %s %s book summary: %s", asset_code, series_code, book_summary_df)  # raise ?
        book_summary_df = pd.concat(books, ignore_index=True) if len(books) > 1 else books[0]
        book_summary_df = book_summary_df.merge(
            asset_series_df[
                [
                    OptionsTerm.SERIES_CODE,
                    OptionsTerm.UNDERLYING_CODE,
                    OptionsTerm.UNDERLYING_ASSET_CLASS,
                    OptionsTerm.UNDERLYING_EXPIRATION_DATE,
                    OptionsTerm.EXCH_TIMESTAMP,
                ]
            ],
            on=OptionsTerm.SERIES_CODE,
            how="left",
        )
        book_summary_df[OptionsTerm.UNDERLYING_CODE] = (
            book_summary_df[OptionsTerm.UNDERLYING_CODE]
            .infer_objects(copy=False)
            .fillna(book_summary_df[OptionsTerm.ASSET_CODE])
        )
        return book_summary_df

    def load_options_history(
        self, asset_code: str, params: RequestParameters | None = None, columns: list | None = None
    ) -> pd.DataFrame:
        """load options history."""
        raise NotImplementedError

    def load_futures_history(
        self, asset_code: str, params: RequestParameters | None = None, columns: list | None = None
    ) -> pd.DataFrame:
        """load futures history"""
        raise NotImplementedError

    def load_futures_book(
        self,
        asset_code: str,
        settlement_datetime: datetime.datetime | None = None,
        timeframe: Timeframe = Timeframe.EOD,
        columns: list | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError

    def load_options_book(
        self,
        asset_code: str,
        settlement_datetime: datetime.datetime | None = None,
        timeframe: Timeframe = Timeframe.EOD,
        columns: list | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError

    def load_options_chain(
        self,
        asset_code: str,
        settlement_datetime: datetime.datetime | None = None,
        expiration_date: datetime.datetime | None = None,
        timeframe: Timeframe = Timeframe.EOD,
        columns: list | None = None,
    ) -> pd.DataFrame | None:
        """Providing option chain by local file system is not supported return None"""
        raise NotImplementedError
