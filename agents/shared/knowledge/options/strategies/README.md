# Strategies — index

↑ Parent: [options/](../README.md)

Multi-leg structures: combine single-leg payoffs
([../payoffs/](../payoffs/README.md)) into a position with a target risk profile. In-repo:
`payoff.py` `chain_payoff` sums per-strike P&L across legs; legs are `OptionsLeg`
(`options_lib/entities/`).

> Source: Hull; [Investopedia: option strategies](https://www.investopedia.com/trading/options-strategies/).

Children:
- [straddle.md](straddle.md) — long/short straddle.

_To add: vertical spreads (bull/bear call/put), strangle, butterfly, condor, calendar,
collar — one file each._
