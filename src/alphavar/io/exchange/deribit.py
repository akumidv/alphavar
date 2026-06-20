"""
Deribit api provider
"""

import concurrent
import datetime
import logging
import re
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from alphavar.core.dictionary import ContractKind, InstrumentKind
from alphavar.io.exchange._abstract_exchange import AbstractExchange, RequestClass
from alphavar.io.exchange.exchange_entities import ExchangeCode
from alphavar.io.exchange.exchange_exception import InstrumentParseError
from alphavar.io.provider import DataEngine, RequestParameters
from alphavar.options.dictionary import (
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


class DeribitAssetKind(EnumCode):
    """Deribit venue-native instrument kinds.

    The enum `value` IS the Deribit wire token (`kind=` query param) and the token under
    which raw update snapshots are stored — singular, venue-spelled (ADR 0001 / R2.2). It
    is *not* the project's canonical kind: map to that via
    ``DeribitExchange.resolve_instrument_kind`` (-> ``InstrumentKind`` + ``ContractKind``).
    """

    FUTURE = "future", "f"
    OPTION = "option", "o"
    SPOT = "spot", "s"  # TODO Crytpo !
    FUTURE_COMBO = "future_combo", "fc"
    OPTION_COMBO = "option_combo", "oc"


DOT_STRIKE_REGEXP = re.compile(r"(\d)d(\d)", flags=re.IGNORECASE)
COLUMNS_TO_CURRENCY = [
    OptionsTerm.ASK,
    OptionsTerm.BID,
    OptionsTerm.LAST,
    OptionsTerm.HIGH_24,
    OptionsTerm.LOW_24,
    OptionsTerm.EXCH_MARK_PRICE,
    OptionsTerm.EXCH_PRICE,
]


class DeribitMarket:
    """Deribit Market data api"""

    def __init__(self, client: RequestClass):
        self.client = client

    def get_instruments(self) -> pd.DataFrame:
        """Retrieves available trading instruments.
        https://docs.deribit.com/#public-get_instruments
        Sample response recorded under tests/unit/io/exchange/fixtures/deribit/.
        """
        response = self.client.request_api("/public/get_instruments")
        asset_codes_df = pd.DataFrame(response["result"])
        return asset_codes_df

    def get_book_summary_by_currency(self, currency: str, kind: DeribitAssetKind | None = None) -> pd.DataFrame:
        """Retrieves the summary information for all instruments for the currency (optionally filtered by kind).
        https://docs.deribit.com/#public-get_book_summary_by_currency
        Sample response recorded under tests/unit/io/exchange/fixtures/deribit/.
        """
        params = {"currency": currency}
        if kind is not None:
            # DeribitAssetKind.value is the venue wire token ('option'/'future'/…) — R2.2.
            params["kind"] = kind.value
        request_timestamp = pd.Timestamp.now(tz=datetime.UTC)
        response = self.client.request_api("/public/get_book_summary_by_currency", params=params)
        book_summary_df = pd.DataFrame(response["result"])
        book_summary_df = self._normalize_book(book_summary_df, request_timestamp)
        return book_summary_df

    @staticmethod
    def _kind_enrichment(row: pd.Series) -> pd.Series:
        exch_symbol_arr = DOT_STRIKE_REGEXP.sub(r"\1.\2", row[OptionsTerm.EXCH_SYMBOL]).split(
            "-"
        )  # for strike DOGE_USDC-7FEB25-0d4064-C  or 3d12
        asset_code = exch_symbol_arr[0]
        row = row.copy(deep=True)
        match len(exch_symbol_arr):
            case 1:  # SPOT
                row[OptionsTerm.ASSET_CODE] = asset_code
                row[OptionsTerm.INSTRUMENT_KIND] = DeribitAssetKind.SPOT.code
                return row
            case 2:  # FUT
                row[OptionsTerm.ASSET_CODE] = asset_code
                expiration_date = parse_expiration_date(exch_symbol_arr[1])
                if expiration_date is None and exch_symbol_arr[1] != "PERPETUAL":
                    raise InstrumentParseError(
                        f"Can not parse {exch_symbol_arr[1]}, "
                        f"None expiration can be only for PERPETUAL: {row}"
                    )
                row[OptionsTerm.EXPIRATION_DATE] = expiration_date
                row[OptionsTerm.INSTRUMENT_KIND] = DeribitAssetKind.FUTURE.code
                return row
            case 3:  # FUT COMBO
                # Second value is strategy for combo, for example FS - future spread
                row[OptionsTerm.ASSET_CODE] = asset_code
                row[OptionsTerm.EXPIRATION_DATE] = parse_expiration_date(exch_symbol_arr[2].split("_")[0])
                row[OptionsTerm.INSTRUMENT_KIND] = DeribitAssetKind.FUTURE_COMBO.code
                return row
            case 4:  # OPT AND OPT COMBO
                row[OptionsTerm.ASSET_CODE] = asset_code
                expiration_date = parse_expiration_date(exch_symbol_arr[1])
                if expiration_date is None:  # OPT COMBO
                    # Second value is strategy for combo, for example PCOND - put condor, CBUT - call butterfly
                    expiration_date = parse_expiration_date(exch_symbol_arr[2])
                    kind = DeribitAssetKind.OPTION_COMBO.code
                    option_type = None
                    strike = None
                    future_expiration_date = None
                else:  # OPT
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
                        if row[OptionsTerm.UNDERLYING_CODE] in [
                            "SYN.EXPIRY",  # Expired already
                            "index_price",
                        ]:  # index price
                            future_expiration_date = None
                        else:
                            logger.error("Syntax error in row:\n%s", row)
                            raise InstrumentParseError(
                                f"Can not get expiration from underlying_index {row[OptionsTerm.UNDERLYING_CODE]}"
                            )
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
                    # `exch_price` is in COLUMNS_TO_CURRENCY now (gets `_raw` + conversion);
                    # our `price` is mirrored from it after enrichment (source_interim_price).
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

    def _normalize_book(self, book_summary_df: pd.DataFrame, request_timestamp: pd.Timestamp) -> pd.DataFrame:
        if book_summary_df.empty:
            return book_summary_df
        book_summary_df[OptionsTerm.REQUEST_TIMESTAMP] = request_timestamp
        rename_columns = {
            "creation_timestamp": OptionsTerm.EXCH_TIMESTAMP,
            "instrument_name": OptionsTerm.EXCH_SYMBOL,  # venue contract string (R4.1.1); asset_code = underlying
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
        book_summary_df = fill_option_price(book_summary_df)  # -> exch_price (venue traded)
        book_summary_df = book_summary_df.apply(self._kind_enrichment, axis="columns", result_type="expand")
        book_summary_df = source_interim_price(book_summary_df)  # price <- exch_price (interim, T23.6)
        return book_summary_df


class DeribitExchange(AbstractExchange):
    """Deribit exchange api"""

    PRODUCT_API_URL: str = "https://www.deribit.com/api/v2"
    TEST_API_URL: str = "https://test.deribit.com/api/v2"
    CURRENCIES: list[str] = ["BTC", "ETH", "USDC", "USDT", "EURR"]
    TASKS_LIMIT: int = 4

    # Venue-native kind token -> canonical (InstrumentKind, ContractKind) (ADR 0001).
    # Combos are not a kind: they carry a vanilla instrument kind + ContractKind.COMBO.
    INSTRUMENT_KIND_MAP: dict[str, tuple[InstrumentKind, ContractKind]] = {
        DeribitAssetKind.OPTION.value: (InstrumentKind.OPTION, ContractKind.VANILLA),
        DeribitAssetKind.FUTURE.value: (InstrumentKind.FUTURE, ContractKind.VANILLA),
        DeribitAssetKind.SPOT.value: (InstrumentKind.SPOT, ContractKind.VANILLA),
        DeribitAssetKind.OPTION_COMBO.value: (InstrumentKind.OPTION, ContractKind.COMBO),
        DeribitAssetKind.FUTURE_COMBO.value: (InstrumentKind.FUTURE, ContractKind.COMBO),
    }

    def __init__(self, engine: DataEngine = DataEngine.PANDAS, api_url: str | None = None):
        """Init"""
        api_url = api_url if api_url else self.PRODUCT_API_URL
        super().__init__(engine, ExchangeCode.DERIBIT.name, api_url=api_url)
        self.market = DeribitMarket(self.client)

    def get_assets_list(self, asset_kind: InstrumentKind) -> list[str]:
        """
        :param asset_kind:
        :return:
        Sample response recorded under tests/unit/io/exchange/fixtures/deribit/.
        """
        asset_codes_df = self.market.get_instruments()
        return [asset_code.upper() for asset_code in asset_codes_df["price_index"].unique()]

    def get_asset_history_years(self, asset_code: str, asset_kind: InstrumentKind, timeframe: Timeframe) -> list[int]:
        """Exchange API does not provide per-year history."""
        raise NotImplementedError

    def get_options_assets_books_snapshot(self, asset_codes: list[str] | str | None = None) -> pd.DataFrame:
        """Get all option snapshot
        Sample response recorded under tests/unit/io/exchange/fixtures/deribit/.
        """
        if asset_codes is None:
            asset_codes = self.CURRENCIES
        elif isinstance(asset_codes, str):
            asset_codes = [asset_codes]
        if len(asset_codes) == 1:
            book_summary_df = self.market.get_book_summary_by_currency(currency=asset_codes[0])
        else:
            books = []
            with ThreadPoolExecutor(max_workers=self.TASKS_LIMIT) as executor:
                job_results = {
                    executor.submit(self.market.get_book_summary_by_currency, currency): currency
                    for currency in asset_codes
                }
                for job_res in concurrent.futures.as_completed(job_results):
                    currency = job_results[job_res]
                    try:
                        book_summary_df = job_res.result()
                    except Exception as err:
                        logger.error("for %s book summary: %s", currency, err)
                        raise
                    books.append(book_summary_df)
            book_summary_df = pd.concat(books, ignore_index=True) if len(books) > 1 else books[0]
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
