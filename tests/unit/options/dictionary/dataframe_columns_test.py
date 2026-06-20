"""Testing dataframe columns integrity"""

from alphavar.options.dictionary import (
    # FuturesColumns as FCl,
    # SpotColumns as SCl,
    OPTION_NON_FUTURES_COLUMN_NAMES,
    OPTION_NON_SPOT_COLUMN_NAMES,
    OptionsTerm,
)


def test_option_non_fut_spot_columns():
    assert isinstance(OPTION_NON_FUTURES_COLUMN_NAMES, list)
    assert OptionsTerm.TIMESTAMP not in OPTION_NON_FUTURES_COLUMN_NAMES
    assert OptionsTerm.STRIKE in OPTION_NON_FUTURES_COLUMN_NAMES
    assert isinstance(OPTION_NON_SPOT_COLUMN_NAMES, list)
    assert OptionsTerm.TIMESTAMP not in OPTION_NON_SPOT_COLUMN_NAMES
    assert OptionsTerm.STRIKE in OPTION_NON_SPOT_COLUMN_NAMES
