""" "Public analytic api class that should hide realization of functions"""

from alphavar.options.analytic_price_class import OptionsAnalyticPrice
from alphavar.options.analytic_risk_class import OptionsAnalyticRisk
from alphavar.options.option_data_class import OptionsData


class OptionsAnalytic:
    """
    Wrapper about analytics modules functions
    """

    def __init__(self, data: OptionsData):
        self._data = data
        self.risk = OptionsAnalyticRisk(data)
        self.price = OptionsAnalyticPrice(data)
