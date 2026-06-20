"""Realisation for option class"""

import plotly.graph_objects as go
from plotly.offline import iplot

from alphavar.options.chart_price_class import ChartPriceClass
from alphavar.options.option_data_class import OptionsData


class ChartClass:
    """Base option chart class that provide possibility to work with option data different way"""

    _data: OptionsData
    price: ChartPriceClass
    figure: go.Figure

    def __init__(self, data: OptionsData, title: str | None = None):
        self._data = data
        self.price = ChartPriceClass(data)
        self._title = title
        self.init()

    def init(self, title: str | None = None):
        """Init new chart"""
        self.price.empty_figure_data()
        self.figure = go.Figure(layout={"title": self._title if title is None else title})

    def show(self):
        """Show prepared data"""
        # data = []
        for price_trace in self.price.figure_data:
            self.figure.add_trace(price_trace)
        # data.extend(self.price.figure_data)
        # self.figure = go.Figure(data=data, title=self._title)
        iplot(self.figure)
