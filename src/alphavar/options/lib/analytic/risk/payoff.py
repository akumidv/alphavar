"""Option Risk Profile functions"""

import pandas as pd

from alphavar.options.dictionary import LegType, OptionsTerm, OptionsType
from alphavar.options.entities import OptionsLeg
from alphavar.options.lib.analytic.risk._risk_entities import RiskColumns as RCl


def _get_premium(df_chain_type_opt: pd.DataFrame, strike: float, leg_type: LegType | None = None) -> float:
    if leg_type is None and OptionsTerm.OPTION_RIGHT not in df_chain_type_opt.columns:
        raise ValueError("Data frame should be with one option type or ser leg_type")
    if leg_type == LegType.FUTURES:
        raise ValueError("Future do not have premium")
    if leg_type is not None:
        df_chain_type_opt = df_chain_type_opt[df_chain_type_opt[OptionsTerm.OPTION_RIGHT] == leg_type.value]
    premium_df = df_chain_type_opt[df_chain_type_opt[OptionsTerm.STRIKE] == strike]
    if premium_df.empty:
        del premium_df
        type_code = (
            OptionsType.CALL.value
            if df_chain_type_opt.iloc[0][OptionsTerm.OPTION_RIGHT] == OptionsType.CALL.value
            else OptionsType.PUT.value
        )
        raise ValueError(f"Data for strike {strike} for and option type {type_code} absent")
    premium = premium_df.iloc[0][OptionsTerm.PRICE]
    del premium_df
    return premium


def _calc_profile(df_opt_type: pd.DataFrame, leg: OptionsLeg, premium: float) -> pd.DataFrame:
    """Calc P&L profile"""
    if leg.type == LegType.OPTIONS_CALL:
        if leg.lots > 0:
            df_opt_type.loc[:, RCl.RISK_PNL.nm] = df_opt_type[OptionsTerm.STRIKE] - leg.strike - premium
            df_opt_type.loc[df_opt_type[OptionsTerm.STRIKE] <= leg.strike, RCl.RISK_PNL.nm] = -premium
        else:
            df_opt_type.loc[:, RCl.RISK_PNL.nm] = premium - (df_opt_type.loc[:, OptionsTerm.STRIKE] - leg.strike)
            df_opt_type.loc[df_opt_type[OptionsTerm.STRIKE] <= leg.strike, RCl.RISK_PNL.nm] = premium
    else:
        if leg.lots > 0:
            df_opt_type.loc[:, RCl.RISK_PNL.nm] = leg.strike - df_opt_type[OptionsTerm.STRIKE] - premium
            df_opt_type.loc[df_opt_type[OptionsTerm.STRIKE] >= leg.strike, RCl.RISK_PNL.nm] = -premium
        else:
            df_opt_type.loc[:, RCl.RISK_PNL.nm] = premium - (leg.strike - df_opt_type.loc[:, OptionsTerm.STRIKE])
            df_opt_type.loc[df_opt_type[OptionsTerm.STRIKE] >= leg.strike, RCl.RISK_PNL.nm] = premium
    df_opt_type.loc[:, RCl.RISK_PNL.nm] *= abs(leg.lots)
    return df_opt_type


def _calc_premium_profile(df_opt_type: pd.DataFrame, leg: OptionsLeg, premium: float) -> pd.DataFrame:
    """Calc the mark-to-market ("today") P&L profile next to the expiration profile.

    ``RISK_PNL`` (from :func:`_calc_profile`) is the payoff at expiration: intrinsic
    value at each strike net of the premium paid. ``RISK_PNL_PREMIUM`` is the current
    P&L if the underlying were at each strike level *now*, valuing the leg with that
    strike's current option price instead of pure intrinsic value — the "today" line on
    a risk graph. For the long side the loss is bounded by the premium at risk; the
    short side mirrors it (max gain = premium received).
    """
    df_opt_type = _calc_profile(df_opt_type, leg, premium)
    if leg.type == LegType.OPTIONS_CALL:
        intrinsic_shift = df_opt_type[OptionsTerm.STRIKE] - leg.strike
    else:
        intrinsic_shift = leg.strike - df_opt_type[OptionsTerm.STRIKE]
    # Per-lot current P&L: intrinsic shift plus the option's current price at that
    # strike, net of premium paid, capped at the premium at risk (long-side max loss).
    pnl_premium = (intrinsic_shift + df_opt_type[OptionsTerm.PRICE] - premium).clip(lower=-premium)
    if leg.lots < 0:  # short: mirror the long profile (max gain = premium received)
        pnl_premium = -pnl_premium
    df_opt_type.loc[:, RCl.RISK_PNL_PREMIUM.nm] = pnl_premium * abs(leg.lots)
    return df_opt_type


# ─────────────────────────────────────────────────────────────────────────────────────
# 4VERIFY (owner): the mark-to-market math in `_calc_premium_profile`
# above is NOT yet verified by the owner — per DEVELOPMENT_REQUIREMENTS D2 all DataFrame
# / math implementations must be explained and explicitly verified by the owner before
# being treated as final. The original pre-2026-06-14 implementation (raised
# NotImplementedError, with several unfinished attempts) is preserved verbatim below for
# that review. `add_intrinsic_and_time_value` is no longer imported — restore the import
# if this body is reinstated.
#
# def _calc_premium_profile(df_opt_type: pd.DataFrame, leg: OptionsLeg, premium: float) -> pd.DataFrame:
#     """Calc premium P&L profile"""
#     raise NotImplementedError
#     if OptionsTerm.INTRINSIC_VALUE not in df_opt_type.columns:
#         df_opt_type = add_intrinsic_and_time_value(df_opt_type)
#     if leg.type == LegType.OPTIONS_CALL:
#         if leg.lots > 0:
#             df_opt_type.loc[:, RCl.RISK_PNL_PREMIUM.nm] = df_opt_type[OptionsTerm.STRIKE] - leg.strike + \
#                                                           (df_opt_type[OptionsTerm.PRICE]) - premium
#             # df_opt_type.loc[df_opt_type[OptionsTerm.STRIKE] <= leg.strike,
#             # RCl.RISK_PNL_PREMIUM.nm] = df_opt_type[OptionsTerm.STRIKE] - leg.strike + \
#             #                            (df_opt_type[OptionsTerm.PRICE]) - premium
#             df_opt_type.loc[df_opt_type[RCl.RISK_PNL_PREMIUM.nm] < -premium, RCl.RISK_PNL_PREMIUM.nm] = -premium
#             # df_opt_type.loc[:, RCl.RISK_PNL_PREMIUM.nm] = (df_opt_type[OptionsTerm.STRIKE] + df_opt_type[
#             #     OptionsTerm.PRICE] - leg.strike - premium) * leg.lots
#             # loss_strike_filter = df_opt_type[OptionsTerm.STRIKE] <= leg.strike
#             # df_opt_type.loc[loss_strike_filter, RCl.RISK_PNL_PREMIUM.nm] = (df_opt_type.loc[
#             #                                                                     loss_strike_filter, OptionsTerm.PRICE] -
#             #                                                                 (leg.strike - df_opt_type.loc[
#             #                                                                     loss_strike_filter, OptionsTerm.STRIKE])
#             #                                                                 - premium) * leg.lots
#         else:
#             df_opt_type.loc[:, RCl.RISK_PNL_PREMIUM.nm] = premium - (df_opt_type.loc[:, OptionsTerm.STRIKE] - leg.strike)
#             df_opt_type.loc[df_opt_type[OptionsTerm.STRIKE] <= leg.strike, RCl.RISK_PNL_PREMIUM.nm] = premium
#
#
#     else:
#         df_opt_type.loc[:, RCl.RISK_PNL_PREMIUM.nm] = (leg.strike - df_opt_type[OptionsTerm.STRIKE] + df_opt_type[
#             OptionsTerm.PRICE] - premium) * leg.lots
#         loss_strike_filter = df_opt_type[OptionsTerm.STRIKE] >= leg.strike
#         df_opt_type.loc[loss_strike_filter, RCl.RISK_PNL_PREMIUM.nm] = (df_opt_type.loc[
#                                                                             loss_strike_filter, OptionsTerm.PRICE] -
#                                                                         (df_opt_type.loc[
#                                                                              loss_strike_filter, OptionsTerm.STRIKE] - leg.strike)
#                                                                         - premium) * leg.lots
#         df_opt_type.loc[
#             df_opt_type[RCl.RISK_PNL_PREMIUM.nm] < -premium * leg.lots, RCl.RISK_PNL_PREMIUM.nm] = -premium * leg.lots
#     df_opt_type = _calc_profile(df_opt_type, leg, premium) # TODO remove
#     df_opt_type.loc[:, RCl.RISK_PNL_PREMIUM.nm] *= abs(leg.lots)
#     return df_opt_type
# ─────────────────────────────────────────────────────────────────────────────────────


def _chain_leg_expiration_risk_profile(df_chain: pd.DataFrame, leg: OptionsLeg) -> pd.DataFrame:
    """Calc PNL Risk profile for leg"""
    type_code = OptionsType.PUT.value if leg.type == LegType.OPTIONS_PUT else OptionsType.CALL.value
    df = df_chain[df_chain[OptionsTerm.OPTION_RIGHT] == type_code].copy()
    if leg.type == LegType.FUTURES:
        df.loc[:, RCl.RISK_PNL.nm] = (df[OptionsTerm.STRIKE] - df[OptionsTerm.UNDERLYING_PRICE]) * leg.lots
        df.loc[:, RCl.RISK_PNL_PREMIUM.nm] = df[RCl.RISK_PNL.nm]
    else:
        premium_df = df[df[OptionsTerm.STRIKE] == leg.strike]
        if premium_df.empty:
            raise ValueError(f"Data for strike {leg.strike} for and option type {leg.type.value} absent")
        premium = premium_df.iloc[0][OptionsTerm.PRICE]
        df = _calc_premium_profile(df, leg, premium)
    df.drop(
        columns=[col for col in df.columns if col not in [OptionsTerm.STRIKE, RCl.RISK_PNL.nm, RCl.RISK_PNL_PREMIUM.nm]],
        inplace=True,
    )
    return df


def chain_payoff(df_chain: pd.DataFrame, legs: list[OptionsLeg]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate options payoff also called as risk profile
    Example of profiles https://www.optionstaxguy.com/risk-profiles
    Explanation https://www.investopedia.com/trading/options-risk-graphs/

    Option risk PNL Profile on expiration date and for current
    Index is Strike values
    """

    legs_dfs = []
    for idx, leg in enumerate(legs):
        df_leg = _chain_leg_expiration_risk_profile(df_chain, leg)
        df_leg.loc[:, RCl.LEG_ID.nm] = f"#{idx}_{leg.type.value}_{leg.strike}_{leg.lots}"
        legs_dfs.append(df_leg)
    if len(legs_dfs) == 0:
        raise ValueError(f"Can not prepared risk profile for {len(legs)} legs number")
    df_legs_risk_profile = pd.concat(legs_dfs, axis="rows", ignore_index=True) if len(legs_dfs) > 1 else legs_dfs[0]
    df_legs_risk_profile.sort_values(by=[OptionsTerm.STRIKE, RCl.LEG_ID.nm], inplace=True)
    df_risk_profile = (
        df_legs_risk_profile.groupby(OptionsTerm.STRIKE, group_keys=False)[[RCl.RISK_PNL.nm, RCl.RISK_PNL_PREMIUM.nm]]
        .agg({RCl.RISK_PNL.nm: "sum", RCl.RISK_PNL_PREMIUM.nm: "sum"})
        .reset_index(drop=False)
    )
    # 4VERIFY (owner): aggregation now sums RISK_PNL_PREMIUM alongside
    # RISK_PNL (2026-06-14). Original RISK_PNL-only aggregation preserved below:
    # df_risk_profile = df_legs_risk_profile.groupby(OptionsTerm.STRIKE, group_keys=False)[
    #     [RCl.RISK_PNL.nm]] \
    #     .agg({RCl.RISK_PNL.nm: 'sum'}) \
    #     .reset_index(drop=False)
    return df_risk_profile, df_legs_risk_profile
