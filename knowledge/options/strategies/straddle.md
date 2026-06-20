# Straddle

↑ Index: [options/strategies/](README.md)

> Source: [Investopedia: straddle](https://www.investopedia.com/terms/s/straddle.asp).

- **Long straddle:** buy a call + a put at the **same strike & expiry** (ATM). Profits
  from large moves in **either** direction; max loss = total premium paid (at K). A
  volatility-long position.
- **Short straddle:** sell both; collects premium, profits if the underlying stays near
  K; large loss on big moves (volatility-short).
- **In-repo:** represented as two `OptionsLeg`s with equal `strike`; `chain_payoff`
  aggregates them (see `tests/.../risk_payoff_test.py::test_chain_pnl_risk_profile_structure_long_straddle`).
