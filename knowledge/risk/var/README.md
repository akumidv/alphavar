# Value at Risk (VaR) — index

↑ Parent: [risk/](../README.md)

> Source: Hull, *Options, Futures, and Other Derivatives* (VaR & Expected Shortfall).

**VaR** = the loss threshold not exceeded with probability `1−α` over a horizon (e.g.
1-day 99%). Key caveat: VaR is **not coherent** (sub-additivity can fail) → prefer/also
report **CVaR / Expected Shortfall** (average loss beyond VaR; coherent).

Children:
- [methods.md](methods.md) — historical, parametric (variance-covariance), Monte-Carlo.
- [cvar-expected-shortfall.md](cvar-expected-shortfall.md) — CVaR / ES.

_alphavar's chosen VaR/CVaR method is TBD — record it here (formula + source) and
owner-verify (D2) before code relies on it._
