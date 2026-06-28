# Tasks — alphavar

Implementation backlog. Format: [keystone tasks convention](keystone/pipelines/tasks.md) —
one line per task, **detail by reference**, no dates, `done` → [TASKS_ARCHIVE.md](TASKS_ARCHIVE.md).

> Constraints: [ARCHITECTURE_REQUIREMENTS.md](../docs/dev/ARCHITECTURE_REQUIREMENTS.md) (R0…R8) ·
> [DEVELOPMENT_REQUIREMENTS.md](DEVELOPMENT_REQUIREMENTS.md) (D1…D7). Every task: `pytest` +
> `ruff` green; any math/DataFrame/architecture change is **not done until owner-verified**
> ([D2 ledger](D2_VERIFICATION.md)).

## Status

Suite green, ruff clean. Forecast (T27) is code-complete & D2-pending; result-chain V1 (T37)
landed. Active focus: D2 verification of the forecast math, architecture remediation from ADR 0004,
then the forecast follow-ups and the P4 capability roadmap.

## Active / blocked / deferred

- T27 · forecast capability area · active · engineer · D2-verify math; build factor-conditional + analogue models · [design](design/forecast/README.md)
- T40 · pin interchange schemas for smile/surface · active · engineer · scalar-less θ output needs pinned interchange schemas · [design](design/forecast/README.md)
- T41 · enforce pure `lib` boundary · active · architect/engineer · move reference storage out of `lib`; add architecture guard · [design](design/architecture-remediation.md)
- T42 · pin options producer contracts · active · architect · enrichment/chain/pricer/validation/risk contracts for users/AI/flow · [design](design/architecture-remediation.md)
- T43 · harden DataFrame transform contracts · active · engineer · fix enrichment force/drop; graph deps; reduce in-place pandas hotspots · [design](design/architecture-remediation.md)
- T44 · finish schema/vocabulary migration · active · architect/engineer · canonical Terms/StrEnum/schemas; isolate legacy shims · [design](design/architecture-remediation.md)
- T29 · surface fitting model (pricer) · active · architect · joint SVI-surface calibration with calendar no-arb · [design](design/domains-roadmap.md)
- T30 · sparse/live smile-shift · active · architect · low-DoF additive-`w` shift of a prior smile; lock open Qs · [design](design/pricer/smile-shift.md)
- T36 · implement planned `knowledge/` concepts · active · engineer · full Greeks + Sortino, then their USAGE skills · [design](design/domains-roadmap.md)
- T28 · unify provider ↔ exchange data path · blocked · architect · one canonical-normalization contract; needs an ADR · [design](design/domains-roadmap.md)
- T31 · spot domain · deferred · architect · `alphavar.spot` over the neutral core · [design](design/domains-roadmap.md)
- T32 · bonds domain · deferred · architect · fixed-income + yield-curve layer · [design](design/domains-roadmap.md)
- T33 · portfolio management · deferred · architect · cross-domain position book + VaR/CVaR · [design](design/domains-roadmap.md)
- T35 · risk layer · deferred · architect · VaR/CVaR/stress from forecast distributions · [design](design/domains-roadmap.md)
- T23.6c · stored-parquet column migration · deferred · engineer · owner-run; tooling ready · [archive](TASKS_ARCHIVE.md)
- T25 · flip `slim_series` on · deferred · engineer · owner-run; shrinks stored files · [archive](TASKS_ARCHIVE.md)

## Done

See [TASKS_ARCHIVE.md](TASKS_ARCHIVE.md).
