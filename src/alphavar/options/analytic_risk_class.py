""" "Public risk analytic api class that should hide realization of functions"""

import pandas as pd

from alphavar.options.entities import OptionsLeg
from alphavar.options.lib.analytic.risk.payoff import chain_payoff
from alphavar.options.option_data_class import OptionsData


class OptionsAnalyticRisk:
    """
    Wrapper about risk analytics modules functions
    """

    def __init__(self, data: OptionsData):
        self._data = data

    def chain_payoff(self, legs: list[OptionsLeg]) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Calculate option risk profile"""
        return chain_payoff(self._data.df_chain, legs)
