from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.chain.price_status import get_chain_atm_strike


def test_get_chain_atm_strike(df_chain):
    atm_strike = get_chain_atm_strike(df_chain)
    assert isinstance(atm_strike, float)
    assert atm_strike in df_chain[OptionsTerm.STRIKE].unique()
    df_chain["_diff"] = (df_chain[OptionsTerm.UNDERLYING_PRICE] - df_chain[OptionsTerm.STRIKE]).abs()
    assert atm_strike == df_chain[df_chain["_diff"] == df_chain["_diff"].min()].iloc[0][OptionsTerm.STRIKE]
