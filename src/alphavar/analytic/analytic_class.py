""""Public analytic api class that should hide realization of functions"""

from alphavar.option_data_class import OptionData

from alphavar.analytic.risk.risk_class import OptionAnalyticRisk
from alphavar.analytic.price.price_class import OptionAnalyticPrice


class OptionAnalytic:
    """
    Wrapper about analytics modules functions
    """

    def __init__(self, data: OptionData):
        self._data = data
        self.risk = OptionAnalyticRisk(data)
        self.price = OptionAnalyticPrice(data)
