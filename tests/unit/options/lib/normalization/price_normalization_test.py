import pandas as pd

from alphavar.options.dictionary import OptionsTerm, OptionsType
from alphavar.options.lib.normalization.price import fill_option_price, source_interim_price


def _quote_df():
    return pd.DataFrame(
        {
            OptionsTerm.OPTION_RIGHT: [OptionsType.CALL] * 7,
            OptionsTerm.LAST: [80, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA],
            OptionsTerm.ASK: [pd.NA, 105, 105, pd.NA, pd.NA, pd.NA, pd.NA],
            OptionsTerm.BID: [pd.NA, 95, pd.NA, 95, pd.NA, pd.NA, pd.NA],
            OptionsTerm.HIGH: [pd.NA, pd.NA, pd.NA, pd.NA, 110, 110, pd.NA],
            OptionsTerm.LOW: [pd.NA, pd.NA, pd.NA, pd.NA, 90, pd.NA, 90],
        }
    )


def test_fill_option_price_targets_exch_price():
    # R4.2: the derived venue price lands in exch_price, not our model `price`.
    df = fill_option_price(_quote_df())
    assert df[OptionsTerm.EXCH_PRICE].notnull().all()
    assert OptionsTerm.PRICE not in df.columns


def test_source_interim_price_mirrors_exch_price():
    df = source_interim_price(fill_option_price(_quote_df()))
    assert df[OptionsTerm.PRICE].notnull().all()
    pd.testing.assert_series_equal(
        df[OptionsTerm.PRICE], df[OptionsTerm.EXCH_PRICE], check_names=False
    )
