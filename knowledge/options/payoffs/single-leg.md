# Single-leg payoffs

↑ Index: [options/payoffs/](README.md)

> Source: [Investopedia risk graphs](https://www.investopedia.com/trading/options-risk-graphs/);
> in-repo `payoff.py` (`_calc_profile`, `_calc_premium_profile`).

At-expiration P&L per lot (premium = price paid/received):
- **Long call:** `max(0, S−K) − premium`. Max loss = premium; upside unbounded.
- **Short call:** `premium − max(0, S−K)`. Max gain = premium; loss unbounded.
- **Long put:** `max(0, K−S) − premium`. Max loss = premium; gain up to `K − premium`.
- **Short put:** `premium − max(0, K−S)`. Max gain = premium; large downside.

Scaled by `abs(lots)`. The mark-to-market ("today") variant uses current option prices
across strikes — **owner-verification pending (D2)**.
