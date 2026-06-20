"""Option data class realisation"""

import datetime

import pandas as pd
from pandas.core.frame import DataFrame

from alphavar.io.provider import AbstractProvider, RequestParameters
from alphavar.options.dictionary import OptionsTerm, Timeframe
from alphavar.options.entities import AssetMeta
from alphavar.options.lib.reference import CONTRACT_KEY_COLUMNS, join_reference_asof


class OptionsData:
    """Option data hide from user provider realisation and allow to share data with different option lib components"""

    _df_hist = None
    _df_fut = None
    _df_chain = None
    _reference = None
    _reference_history = None
    _reference_loaded = False

    def __init__(
        self,
        provider: AbstractProvider,
        asset_code: str,
        provider_params: RequestParameters | None = None,
        option_columns: list | None = None,
        future_columns: list | None = None,
        drop_na_price: bool = True,
    ):
        self._provider = provider
        self._asset_code = asset_code
        self._provider_params = provider_params
        self._opt_columns = option_columns if isinstance(option_columns, list) else AbstractProvider.options_columns
        self._fut_columns = future_columns if isinstance(future_columns, list) else AbstractProvider.futures_columns
        # Drop option rows with no price on load (unpriceable/non-tradable; they break
        # downstream pricing/analytics). Explicit + overridable (was a silent dropna).
        self._drop_na_price = drop_na_price

    @property
    def asset_code(self) -> str:
        """Underlying asset code"""
        return self._asset_code

    @property
    def period_from(self) -> int | datetime.date | datetime.datetime | None:
        """Option data period from"""
        return self._provider_params.period_from

    @property
    def period_to(self) -> int | datetime.date | datetime.datetime | None:
        """Option data period to"""
        return self._provider_params.period_to

    @property
    def timeframe(self) -> Timeframe:
        """Option data timeframe"""
        return self._provider_params.timeframe

    @property
    def df_hist(self) -> pd.DataFrame:
        """Option dataframe getter"""
        if self._df_hist is None:
            opt_params: RequestParameters = RequestParameters(
                period_from=self._provider_params.period_from,
                period_to=self._provider_params.period_to,
                timeframe=self._provider_params.timeframe,
            )
            self._df_hist = self._provider.load_options_history(
                self._asset_code, params=opt_params, columns=self._opt_columns
            )
            # Reattach the reference layer if the stored series is slim (T25). No-op on a wide
            # frame (every reference column already present) and when no reference is stored.
            self._df_hist = self._restore_reference(self._df_hist)
            # 4VERIFY (owner, D2): explicit, opt-out drop of price-less rows
            # (was an unconditional silent `dropna(inplace=True)` here — same default).
            if self._drop_na_price and OptionsTerm.PRICE in self._df_hist.columns:
                self._df_hist = self._df_hist.dropna(subset=[OptionsTerm.PRICE])
        return self._df_hist

    @df_hist.setter
    def df_hist(self, df: DataFrame) -> None:
        """Option dataframe setter"""
        self._df_hist: DataFrame = df

    @property
    def df_fut(self) -> DataFrame:
        """Future dataframe getter"""
        if self._df_fut is None:
            fut_params: RequestParameters = RequestParameters(
                period_from=self._provider_params.period_from,
                period_to=self._provider_params.period_to,
                timeframe=self._provider_params.timeframe,
            )
            self._df_fut = self._provider.load_futures_history(
                self._asset_code, params=fut_params, columns=self._fut_columns
            )
        return self._df_fut

    @df_fut.setter
    def df_fut(self, df: pd.DataFrame) -> None:
        """Future dataframe setter"""
        self._df_fut = df

    def update_option_chain(
        self,
        settlement_date: datetime.datetime | None = None,
        expiration_date: datetime.datetime | None = None,
    ) -> bool:
        """Update option chain by api request if it supported by provider"""
        df_chain: DataFrame | None = self._provider.load_options_chain(
            self.asset_code, settlement_date, expiration_date
        )
        if df_chain is None:
            return False
        self._df_chain: DataFrame = df_chain
        return True

    @property
    def df_chain(self) -> pd.DataFrame:
        """Chain dataframe getter"""
        return self._df_chain

    @df_chain.setter
    def df_chain(self, df_chain):
        """Chain dataframe setter"""
        self._df_chain = df_chain

    def _ensure_reference(self) -> None:
        if not self._reference_loaded:
            # `load_reference` is an optional provider capability (AbstractProvider supplies a
            # no-reference default); tolerate a duck-typed provider that doesn't implement it.
            load_reference = getattr(self._provider, "load_reference", None)
            if load_reference is not None:
                self._reference, self._reference_history = load_reference(self._asset_code)
            if self._reference_history is None:
                self._reference_history = pd.DataFrame()
            self._reference_loaded = True

    @property
    def reference(self) -> AssetMeta | None:
        """Asset-level reference (R4.6, T25); ``None`` when the stored data carries no reference
        layer yet (e.g. pre-migration wide files)."""
        self._ensure_reference()
        return self._reference

    @property
    def reference_history(self) -> pd.DataFrame:
        """Contract-level SCD-2 reference history; empty frame when none is stored."""
        self._ensure_reference()
        return self._reference_history

    def _restore_reference(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rebuild the wide frame from a slim stored series + the reference sidecar (T25): the
        contract-level reference as of each row's timestamp, then the asset-level constants. Only
        absent columns are filled, so this is a no-op on an already-wide frame or when no
        reference is stored — making slim and legacy-wide files read identically."""
        if self.reference is None:
            return df
        if not self.reference_history.empty and OptionsTerm.TIMESTAMP in df.columns:
            key_cols = [c for c in CONTRACT_KEY_COLUMNS if c in df.columns]
            if key_cols:
                df = join_reference_asof(df, self.reference_history, key_cols, OptionsTerm.TIMESTAMP)
        return self.reapply_reference(df)

    def reapply_reference(self, df: pd.DataFrame) -> pd.DataFrame:
        """Broadcast the asset-level reference back onto ``df`` (R4.6, T25). Idempotent and safe
        on either form: a no-op when no reference is stored (today's wide files) or when a column
        is already present, so it never double-writes a value the frame already carries."""
        meta = self.reference
        if meta is None:
            return df
        df = df.copy()
        for field, value in meta.model_dump().items():
            if value is not None and field not in df.columns:
                df[field] = value
        return df
