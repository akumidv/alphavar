"""
Prepare data for option chain - options with the same date and expiration date
"""

from alphavar.options.dictionary import OptionsPriceStatus, OptionsTerm, OptionsType


def get_chain_atm_strike(df_chain):
    """Get strike atm"""
    atm_nearest_strikes = get_chain_atm_nearest_strikes(df_chain)
    atm_strike = atm_nearest_strikes[0]
    return atm_strike


def get_chain_atm_nearest_strikes(df_chain):
    """Get strikes sorted as nearest to atm (for showing desk for example)"""
    atm_nearest_strikes = (
        df_chain.assign(_diff=lambda x: abs(x[OptionsTerm.UNDERLYING_PRICE] - x[OptionsTerm.STRIKE]))
        .sort_values(by="_diff")[OptionsTerm.STRIKE]
        .unique()
    )
    return atm_nearest_strikes


def get_chain_atm_itm_otm(df_chain):
    """
    ITM In the Money
    OTM Out of the Money
    ATM At the Money
    """
    atm_strike = get_chain_atm_strike(df_chain)
    df_chain.loc[:, OptionsTerm.PRICE_STATUS] = OptionsPriceStatus.OTM.code
    df_chain.loc[df_chain[OptionsTerm.STRIKE] == atm_strike, OptionsTerm.PRICE_STATUS] = OptionsPriceStatus.ATM.code
    df_chain.loc[
        (df_chain[OptionsTerm.STRIKE] < atm_strike) & (df_chain[OptionsTerm.OPTION_RIGHT] == OptionsType.CALL.value),
        OptionsTerm.PRICE_STATUS,
    ] = OptionsPriceStatus.ITM.code
    df_chain.loc[
        (df_chain[OptionsTerm.STRIKE] > atm_strike) & (df_chain[OptionsTerm.OPTION_RIGHT] == OptionsType.PUT.value),
        OptionsTerm.PRICE_STATUS,
    ] = OptionsPriceStatus.ITM.code
    return df_chain[OptionsTerm.PRICE_STATUS]
