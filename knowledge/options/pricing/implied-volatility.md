# Implied volatility (IV)

↑ Index: [options/pricing/](README.md)

> Sources: Hull (implied volatility); in-repo dictionary v2 (column semantics).

- **Definition:** the volatility σ that makes a pricing model (Black-Scholes; **Black-76**
  for futures-settled options) reproduce the observed market price. Solved numerically
  (e.g. Newton-Raphson / bisection on price(σ)).
- **Smile / surface:** IV varies by strike and expiry (volatility smile/skew); a fitted,
  no-arbitrage surface is the basis for normalized `iv`.
- **alphavar semantics:** `iv` = our normalized/model IV; the venue's quoted IV is
  `exch_iv` / `exch_mark_iv` (R4). _Solver & surface fit TBD; owner-verify (D2)._
