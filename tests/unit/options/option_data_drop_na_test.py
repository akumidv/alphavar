"""T14 equivalence (D2): the `df_hist` price-drop is now an explicit, overridable flag.
Default (drop_na_price=True) reproduces the prior silent `dropna(subset=[PRICE])`; the
flag can opt out. Pins both branches.
"""

import pandas as pd

from alphavar.io.provider import RequestParameters
from alphavar.options.dictionary import OptionsTerm
from alphavar.options.option_data_class import OptionsData


class _StubProvider:
    """Minimal duck-typed provider returning a fixed option-history frame."""

    options_columns: list = []
    futures_columns: list = []

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def load_options_history(self, asset_code, params, columns):  # noqa: ARG002
        return self._df.copy()


def _df_with_nan_price() -> pd.DataFrame:
    return pd.DataFrame(
        {OptionsTerm.PRICE: [1.0, None, 3.0], OptionsTerm.STRIKE: [10.0, 20.0, 30.0]}
    )


def test_drop_na_price_default_drops_priceless_rows():
    data = OptionsData(_StubProvider(_df_with_nan_price()), "BTC", RequestParameters())
    assert data.df_hist[OptionsTerm.PRICE].tolist() == [1.0, 3.0]


def test_drop_na_price_false_keeps_all_rows():
    data = OptionsData(
        _StubProvider(_df_with_nan_price()), "BTC", RequestParameters(), drop_na_price=False
    )
    assert len(data.df_hist) == 3
    assert data.df_hist[OptionsTerm.PRICE].isna().sum() == 1
