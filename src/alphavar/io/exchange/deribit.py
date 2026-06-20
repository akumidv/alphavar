"""
Deribit api provider
"""

import concurrent
import datetime
import logging
import re
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from alphavar.core.dictionary import InstrumentKind
from alphavar.io.exchange._abstract_exchange import AbstractExchange, RequestClass
from alphavar.io.exchange.exchange_entities import ExchangeCode
from alphavar.io.exchange.exchange_exception import InstrumentParseError
from alphavar.io.provider import DataEngine, RequestParameters
from alphavar.options.dictionary import (
    ContractKind,
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
    def _enrich_kinds(df: pd.DataFrame) -> pd.DataFrame:
        """Parse the venue ``exch_symbol`` into asset_code / instrument_kind / expiration /
        strike / option_right / underlying-expiration, vectorized by token count (T20).

        Replaces the old row-wise ``df.apply(_kind_enrichment, axis="columns")`` (a deep copy
        per ~5000 instruments — the dominant ETL cost) with boolean masks. Provably equivalent
        to that logic: ``deribit_normalize_characterization_test`` (D2 Type A).

        Token count ⇒ kind: 1=spot, 2=future, 3=future_combo, 4=option/option_combo (combo when
        the contract's date slot doesn't parse — e.g. ``BTC-PCOND-…``). Example option symbol
        (after the ``NdM`` → ``N.M`` strike fix): ``DOGE_USDC-7FEB25-0.4064-C``.
        """
        exch = df[OptionsTerm.EXCH_SYMBOL].astype(str).str.replace(DOT_STRIKE_REGEXP, r"\1.\2", regex=True)
        parts = exch.str.split("-")
        n = parts.str.len()
        p0, p1, p2, p3 = parts.str[0], parts.str[1], parts.str[2], parts.str[3]

        m1, m2, m3, m4 = n == 1, n == 2, n == 3, n == 4
        if not (m1 | m2 | m3 | m4).all():
            raise InstrumentParseError(
                f"Can parse instrument_name {df.loc[~(m1 | m2 | m3 | m4), OptionsTerm.EXCH_SYMBOL].tolist()}"
            )

        df[OptionsTerm.ASSET_CODE] = p0

        # 4-part split into option vs option_combo: a combo's first slot is a strategy, not a date.
        exp1 = pd.Series(index=df.index, dtype=object)
        exp1[m4] = p1[m4].map(parse_expiration_date)
        m_opt = m4 & exp1.notna()
        m_combo = m4 & exp1.isna()

        kind = pd.Series(index=df.index, dtype=object)
        kind[m1] = DeribitAssetKind.SPOT.code
        kind[m2] = DeribitAssetKind.FUTURE.code
        kind[m3] = DeribitAssetKind.FUTURE_COMBO.code
        kind[m_opt] = DeribitAssetKind.OPTION.code
        kind[m_combo] = DeribitAssetKind.OPTION_COMBO.code
        df[OptionsTerm.INSTRUMENT_KIND] = kind

        if (m2 | m3 | m4).any():
            expiration = pd.Series(index=df.index, dtype=object)
            expiration[m2] = p1[m2].map(parse_expiration_date)  # None only for PERPETUAL
            m2_bad = m2 & expiration.isna() & (p1 != "PERPETUAL")
            if m2_bad.any():
                raise InstrumentParseError(
                    f"Can not parse {p1[m2_bad].tolist()}, None expiration can be only for PERPETUAL"
                )
            if m3.any():  # the slice is empty/float-typed otherwise → .str would raise
                expiration[m3] = p2[m3].str.split("_").str[0].map(parse_expiration_date)
            if m_opt.any():
                expiration[m_opt] = exp1[m_opt]
            if m_combo.any():
                expiration[m_combo] = p2[m_combo].map(parse_expiration_date)
            df[OptionsTerm.EXPIRATION_DATE] = pd.to_datetime(expiration, utc=True)

        if m4.any():
            # option-only fields; option_combo rows keep them empty (as the old code set None)
            right_tokens = p3[m_opt]
            bad_right = ~right_tokens.isin(["C", "P"])
            if bad_right.any():
                raise InstrumentParseError(f"Unknown option type {right_tokens[bad_right].tolist()}")
            option_right = pd.Series(index=df.index, dtype=object)
            option_right[m_opt] = right_tokens.map({"C": OptionsType.CALL.code, "P": OptionsType.PUT.code})
            df[OptionsTerm.OPTION_RIGHT] = option_right

            strike = pd.Series(index=df.index, dtype="float64")
            strike[m_opt] = p2[m_opt].astype(float)
            df[OptionsTerm.STRIKE] = strike

            und_exp = pd.Series(index=df.index, dtype=object)
            if m_opt.any():  # only real options carry an underlying; combos never read the column
                und = df[OptionsTerm.UNDERLYING_CODE]
                und_parts = und.str.split("-")
                m_und2 = m_opt & (und_parts.str.len() == 2)
                m_und_bad = m_opt & ~m_und2 & ~und.isin(["SYN.EXPIRY", "index_price"])  # else None
                if m_und_bad.any():
                    raise InstrumentParseError(
                        f"Can not get expiration from underlying_index {und[m_und_bad].tolist()}"
                    )
                und_exp[m_und2] = und_parts[m_und2].str[1].map(parse_expiration_date)
            df[OptionsTerm.UNDERLYING_EXPIRATION_DATE] = pd.to_datetime(und_exp, utc=True)

            # Currency conversion (option/option_combo with a same-currency, priced contract):
            # `exch_price` is in COLUMNS_TO_CURRENCY, so it gets `_raw` + conversion; our `price`
            # is mirrored from it afterwards (source_interim_price). A truthy edp matches the old
            # `if row[col]` / `if edp` (NaN is truthy → kept, only an exact 0 is skipped).
            m_conv = m4 & (df["base_currency"] == df["quote_currency"])
            if "estimated_delivery_price" in df.columns:
                edp = df["estimated_delivery_price"]
                m_conv = m_conv & (edp != 0)
                if m_conv.any():
                    for col in COLUMNS_TO_CURRENCY:
                        if col in df.columns:
                            df.loc[m_conv, f"{col}{AbstractExchange.RAW_SUFFIX}"] = df.loc[m_conv, col]
                            m_mul = m_conv & (df[col] != 0)
                            df.loc[m_mul, col] = df.loc[m_mul, col] * edp[m_mul]
                    if OptionsTerm.VOLUME_NOTIONAL in df.columns and "volume_usd" in df.columns:
                        m_vn = m_conv & df[OptionsTerm.VOLUME_NOTIONAL].isna()
                        df.loc[m_vn, OptionsTerm.VOLUME_NOTIONAL] = df.loc[m_vn, "volume_usd"]

        return df

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
        book_summary_df = book_summary_df.rename(columns=rename_columns)  # no inplace (R8/Polars readiness)
        book_summary_df = df_columns_to_timestamp(book_summary_df, columns=[OptionsTerm.EXCH_TIMESTAMP], unit="ms")
        book_summary_df[OptionsTerm.TIMESTAMP] = book_summary_df[OptionsTerm.EXCH_TIMESTAMP].copy()
        book_summary_df = normalize_timestamp(book_summary_df, columns=[OptionsTerm.TIMESTAMP], freq="1s")
        book_summary_df = fill_option_price(book_summary_df)  # -> exch_price (venue traded)
        book_summary_df = self._enrich_kinds(book_summary_df)  # vectorized (T20)
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
