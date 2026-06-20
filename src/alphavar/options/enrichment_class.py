"""Public api class that should hide realization of functions"""

from collections.abc import Callable
from typing import Self

import pandas as pd

from alphavar.options.dictionary import OPTION_COLUMN_DEPENDENCIES, OptionsTerm
from alphavar.options.lib.enrichment._option_with_future import join_option_with_future
from alphavar.options.lib.enrichment.price import add_atm_itm_otm_by_chain, add_intrinsic_and_time_value
from alphavar.options.option_data_class import OptionsData


class OptionsEnrichment:
    """
    Wrapper about enrichment module function
    methods
      - with 'get' - return new columns or option dataframe
      - with 'add' - add columns to option dataframe and return enrichment instance itself to use in chain

    Column names are plain strings from the ``OptionsTerm`` registry (T23.1).
    """

    _COL_TO_ENRICH_FUNC_MAP: dict[str, Callable] = {
        OptionsTerm.UNDERLYING_PRICE: join_option_with_future,
        OptionsTerm.INTRINSIC_VALUE: add_intrinsic_and_time_value,
        OptionsTerm.TIMED_VALUE: add_intrinsic_and_time_value,
        OptionsTerm.PRICE_STATUS: add_atm_itm_otm_by_chain,
    }

    def __init__(self, data: OptionsData):
        self.data = data

    def enrich_options(self, columns: str | list[str], force: bool = False) -> pd.DataFrame:
        """Enrich options by column name and return dataframe"""
        if not isinstance(columns, list):
            columns = [columns]
        enrich_columns = [col for col in columns if col in self._COL_TO_ENRICH_FUNC_MAP]
        if len(enrich_columns) == 0:
            return self.data.df_hist
        missed_columns = [col for col in columns if col not in enrich_columns and col not in self.data.df_hist.columns]
        if len(missed_columns) != 0:
            raise KeyError(f"It is not possible to add columns: {missed_columns}")
        if force:
            drop_columns = [col for col in enrich_columns if col in self.data.df_hist.columns]
            if drop_columns:
                self.data.df_hist.drop(columns=[drop_columns], inplace=True)
        enrich_columns = self._prepare_order_of_columns_enrichment(enrich_columns)
        for column_name in enrich_columns:
            self._enrichment_fabric(column_name, force=False)
        return self.data.df_hist

    def _prepare_order_of_columns_enrichment(self, columns: list[str]) -> list[str]:
        """Should be improved to prepare order by search graph optimal path"""
        enrich_columns = []
        for col in columns:
            dependencies = self._get_dependencies(col)
            enrich_columns.extend(dependencies)
        enrich_columns_sorted = enrich_columns[:]
        enrich_columns_sorted.sort(key=lambda x: enrich_columns.count(x), reverse=True)
        enrich_columns_wo_dub = []
        for col in enrich_columns_sorted:
            if col not in enrich_columns_wo_dub:
                enrich_columns_wo_dub.append(col)
        return enrich_columns_wo_dub

    def _get_dependencies(self, col: str, iteration: int = 0, source_column: None | str = None) -> list[str]:
        """Prepare chain of dependencies"""
        if source_column is None:
            source_column = col
        if iteration > 10:
            raise RecursionError(f"Can prepare chain due too deep recursion ({iteration}) for {col}")
        dependencies = OPTION_COLUMN_DEPENDENCIES.get(col)
        res_dependencies = [col]
        if dependencies is None:
            return res_dependencies
        for dependent_by_col in dependencies:
            if dependent_by_col == source_column or dependent_by_col in res_dependencies:
                continue
            dep = self._get_dependencies(dependent_by_col, iteration + 1, source_column)
            res_dependencies.extend(dep)
        return res_dependencies

    def add_column(self, column_name: str, force: bool = False) -> Self:
        """Add column data and return self for allow use chain model to enrich data,
        but do not generate graph path to add dependencies columns early. Should be
        controlled manually"""
        self._enrichment_fabric(column_name, force)
        return self

    def get_with_column(self, column_name: str, force: bool = False) -> Self:
        """Add column data and return dataframe"""
        self._enrichment_fabric(column_name, force)
        return self.data.df_hist

    def _enrichment_fabric(self, column_name: str, force: bool = False):
        """Fabric to enrich"""
        if column_name in self.data.df_hist.columns:
            if force:
                self.data.df_hist.drop(columns=column_name, inplace=True)
            else:
                return
        call_func: Callable = self._COL_TO_ENRICH_FUNC_MAP.get(column_name)
        if call_func is None:
            raise KeyError(f"Do not have enrichment function for {column_name}")
        if column_name == OptionsTerm.UNDERLYING_PRICE:
            self.data.df_hist = join_option_with_future(self.data.df_hist, self.data.df_fut)
        else:
            self.data.df_hist = call_func(self.data.df_hist)

    # def get_joint_option_with_future(self) -> pd.DataFrame:
    #     """Return new option data with correspondent future columns"""
    #     if Ocl.UNDERLYING_PRICE.nm in self._data.df_hist.columns:
    #         return self._data.df_hist
    #     return join_option_with_future(self._data.df_hist, self._data.df_fut)
    #
    # def add_future(self) -> Self:
    #     """Update option data with correspondent future columns"""
    #     if Ocl.UNDERLYING_PRICE.nm in self._data.df_hist.columns:
    #         return self._data.df_hist
    #     self._data.df_hist = self.get_joint_option_with_future()
    #     return self
    #
    # def add_intrinsic_and_time_value(self) -> Self:
    #     """Add columns with intrinsic and time value, also join future if data is not enough"""
    #     if Ocl.INTRINSIC_VALUE.nm in self._data.df_hist.columns:
    #         return self
    #     if Ocl.UNDERLYING_PRICE.nm not in self._data.df_hist.columns:
    #         self.add_future()
    #     self._data.df_hist = add_intrinsic_and_time_value(self._data.df_hist)
    #     return self
    #
    # def add_atm_itm_otm(self) -> Self:
    #     """Add column with ATM, OTM, ITM values"""
    #     if Ocl.UNDERLYING_PRICE.nm not in self._data.df_hist.columns:
    #         self.add_future()
    #     if Ocl.PRICE_STATUS.nm in self._data.df_hist.columns:
    #         return self
    #     self._data.df_hist = add_atm_itm_otm_by_chain(self._data.df_hist)
    #     return self
