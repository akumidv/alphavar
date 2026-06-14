# Portfolio management — knowledge index

↑ Parent: [knowledge/](../README.md)

> Sources: Markowitz, *Portfolio Selection* (1952);
> [Investopedia: MPT](https://www.investopedia.com/terms/m/modernportfoliotheory.asp);
> Hull (risk aggregation). _Portfolio-level features are a project goal; code TBD._

Concepts (split into entity files as they are fleshed out):
- **Position vs portfolio:** a set of legs/positions across instruments & underlyings;
  P&L and risk (Greeks, VaR) aggregate across them.
- **Diversification / MPT:** return-vs-variance trade-off; correlations reduce portfolio
  variance; efficient frontier.
- **Risk budgeting:** allocate risk (VaR/vega/delta limits), hedge net Greeks
  (delta-neutral, vega-managed). See [../risk/](../risk/README.md).
- **Sizing:** fixed-fractional; Kelly as an upper bound (use fractional Kelly).

Relation to alphavar: the facade composes per-underlying data (ARCHITECTURE_REQUIREMENTS
R3); portfolio aggregation sits above per-underlying analytics; reference-data
normalization (TASKS T25) underpins multi-instrument joins.

_To add (one file each as designed): `mpt.md`, `risk-budgeting.md`, `position-sizing.md` —
owner-verify (D2) any formulae._
