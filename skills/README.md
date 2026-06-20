# `skills/` — alphavar USAGE layer

How an AI assistant **uses alphavar** to solve a user's task. This is the **USAGE** layer
(see [_forge/keystone/README.md](../_forge/keystone/README.md) §2): it points *outward* —
built to travel into a downstream project that consumes alphavar, not to develop alphavar
itself (that is `_forge/`).

alphavar's archetype is **`package`**, so the keystone requirement applies: USAGE is a
**domain-concept → implementing-function map**, not a bare API reference and not
free-standing knowledge (see
[ARCHETYPES.md](../_forge/keystone/ARCHETYPES.md) → "the domain-concept → function map").

## The unit of USAGE: concept → function → how to apply

Each skill connects three things, all **verified against `src/`**:

1. **The domain concept** — what it is, sourced (e.g. a volatility smile, VaR, a Greek).
2. **The implementing function** — the real public class/function in `alphavar.*` that
   computes it.
3. **How to apply it** — inputs, units/conventions, failure modes, a worked example.

A concept with **no** implementing function yet is a *gap* — record it as a design/impl
task in [`../_forge/TASKS.md`](../_forge/TASKS.md), do not document it here as if it exists.

## Map (domain concept → alphavar entry point)

> Verify each entry against `src/` before relying on it — the public surface drifts.

| Domain concept | alphavar entry point (verified) | Skill |
|---|---|---|
| An option (single contract) | `alphavar.Option` | — |
| Option chain (strikes × expiries) | `alphavar.options.chain_class.OptionsChain` | [option-chain](option-chain/SKILL.md) |
| Pricing & implied volatility (Black-76) | `alphavar.options.pricer_class.OptionsPricer` (`add_iv`/`add_price`/`get_iv`); `lib.pricer.black_scholes` (`bs_forward_price`, `bs_vega`, `implied_vol`) | [pricing-and-iv](pricing-and-iv/SKILL.md) |
| Volatility smile fit | `alphavar.options.lib.pricer.smile` — `SVISmile` / `SABRSmile` / `QuadraticSmile` (or `OptionsPricer.fit_smile`) | [fit-volatility-smile](fit-volatility-smile/SKILL.md) |
| Intrinsic / time value, moneyness | `lib.enrichment.price.add_intrinsic_and_time_value`; `lib.chain.price_status` | [option-chain](option-chain/SKILL.md) |
| Strategy payoff (single-leg, straddle, …) | `alphavar.options.analytic_risk_class.OptionsAnalyticRisk.chain_payoff(legs)` + `OptionsLeg` | [strategy-payoff](strategy-payoff/SKILL.md) |
| Exchange data (Deribit / Binance / MOEX) | `alphavar.io.exchange.*` — `DeribitExchange` / `BinanceExchange` / `MoexExchange` | [data-sources](data-sources/SKILL.md) |

### Concept gaps — knowledge with **no** implementing function yet

Per the keystone rule these are **not USAGE** — they are design/impl tasks
([`../_forge/TASKS.md`](../_forge/TASKS.md)), not skills, until the function exists:

| Concept | Status in `src/` |
|---|---|
| Full Greeks (delta/gamma/theta/rho) | only `bs_vega` exists; the rest are not implemented |
| VaR (historical / parametric / Monte-Carlo) | not implemented |
| CVaR / Expected Shortfall | not implemented |
| Sortino ratio | not implemented |

(When one lands, add a `concept → function → how to apply` skill and move it up into the
map above.)

## Authoring a USAGE skill

A skill is `<name>/SKILL.md` (frontmatter + instruction), the cross-agent format
([keystone §7](../_forge/keystone/README.md)). For a `package`, **no USAGE `tools/`** —
the skill calls the public API directly. Keep it: the concept (sourced), the exact
function (verified), inputs/units/failure modes, and one runnable example.
