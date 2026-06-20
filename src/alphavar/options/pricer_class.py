"""Black-76 pricer facade component (R3, T21).

Aggregated by ``Option`` over the shared ``OptionsData`` (like enrichment/chain/analytic).
Pure math lives in ``options.lib.pricer``; this class only orchestrates df columns.

Requires ``underlying_price`` (the forward) on ``df_hist`` — enrich it first
(``Option.enrichment.add_column(OptionsTerm.UNDERLYING_PRICE)``) when loading raw options.
"""
from typing import Self

import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.pricer._enrich import add_fair_price, add_model_iv
from alphavar.options.option_data_class import OptionsData


class OptionsPricer:
    """Our Black-76 model output (price / IV) over OptionsData."""

    def __init__(self, data: OptionsData):
        self.data = data

    def add_iv(self, market_col: str = OptionsTerm.EXCH_MARK_PRICE, rate: float = 0.0) -> Self:
        """Write ``iv`` = our implied vol of ``market_col`` (default the venue mark price)."""
        self.data.df_hist = add_model_iv(self.data.df_hist, market_col=market_col, rate=rate)
        return self

    def add_price(self, vol_col: str = OptionsTerm.IV, rate: float = 0.0) -> Self:
        """Write ``price`` = Black-76 fair price from the vol in ``vol_col`` (default ``iv``)."""
        self.data.df_hist = add_fair_price(self.data.df_hist, vol_col=vol_col, rate=rate)
        return self

    def get_iv(self, market_col: str = OptionsTerm.EXCH_MARK_PRICE, rate: float = 0.0) -> pd.DataFrame:
        """Compute and return ``df_hist`` with the ``iv`` column added."""
        return self.add_iv(market_col=market_col, rate=rate).data.df_hist
