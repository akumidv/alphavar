# Payoffs — index

↑ Parent: [options/](../README.md)

P&L of a position as a function of the underlying price. In-repo:
`src/alphavar/options_lib/analytic/risk/payoff.py`.

Two curves per position:
- **At expiration** (`risk_pnl`) — intrinsic payoff minus premium (hockey-stick).
- **"Today" / mark-to-market** (`risk_pnl_premium`) — current value across levels.
  **Math pending owner verification (D2 / TASKS T14b).**

Children:
- [single-leg.md](single-leg.md) — long/short call & put profiles.

_Multi-leg combinations live under [../strategies/](../strategies/README.md)._
