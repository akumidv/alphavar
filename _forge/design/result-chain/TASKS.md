# Design tasks — result chain & `alphavar.flow`

> **This is the DESIGN backlog** for the [result-chain concept](README.md) — *separate from the
> implementation backlog* ([`agents/_dev/TASKS.md`](../../TASKS.md)). A task here is
> "produce a design decision recorded in this concept folder", **not** code. Implementation tasks are
> only created once the relevant design tasks are *decided* and folded into [ADR 0003](../../../docs/dev/decisions/0003-composable-result-chain.md).
>
> IDs reuse the open-point numbering (A* = Layer A / flow mechanics, B* = Layer B / planner, X* =
> cross-cutting). Status: `[x]` decided · `[~]` leaning · `[ ]` open. Detail lives in the layer files.

## Decided (this round) — keep, don't re-litigate
- [x] **A0** Module = `alphavar.flow` (+ `composer` inside). → [flow-module](flow-module.md)
- [x] **A1** No `ResultMeta` entity — contract describes scalar I/O; provenance → `flow.RunRecord`.
- [x] **A3** Lineage collapsed into `flow.RunRecord` (not on results).
- [x] **A7** `flow` non-privileged — compatibility lives in descriptions; user can assemble by hand.
- [x] **A8** A `kind` is a contract, not forced decomposition — consolidated producers stay; intermediate
      interchange is opt-in.
- [x] **A9** Layering (lib `df+params→df` / class / flow) + **two shapes** (Shape 1 enrichment via
      column-deps · Shape 2 reduction = new-kind frame).
- [~] **A2** Registry = Python code (binds functions + pandera schemas). *(open sub-tasks below)*
- [~] **A4** Interchange = tidy frame; keep wide `to_frame()` as human render.
- [~] **B3** `Plan` = declarative data (YAML/dict), validated at load.

## Layer A — flow mechanics (design before the first build)
- [ ] **A2a** Define the `Contract` shape in code: input kinds, `ParamSpec`, output frame-schema +
      scalar-spec — concrete dataclass/decorator form.
- [ ] **A2b** Acyclicity / validation rules for the registry (and how a missing kind is reported).
- [ ] **A4a** The pinned pandera schema per Shape-2 kind (start: `ForecastDistributionSchema` =
      `quantile|value|change`); the quantile-grid convention for `to_interchange()`.
- [ ] **Sh1** Formalize Shape-1 contracts: generalize `OPTION_COLUMN_DEPENDENCIES` (column → required
      columns) to carry enrichment params + Shape-1 compatibility in the registry.
- [ ] **A5** Where neutral chain terms live (`quantile`, `value`, `horizon_years`, `confidence`,
      `target`, `model`, `engine`): new neutral registry vs. extend `core.dictionary.Term`.
- [ ] **A6** How an input kind expresses a **data envelope** ("the board over period P"), so Layer B
      can derive the requirement backward.
- [ ] **Res** Resolver execution semantics: shared-node caching/memoization, eager vs lazy, error /
      partial-failure handling.
- [ ] **Run** `flow.RunRecord` format (provenance/lineage of a run; reproducibility from `seed`).
- [ ] **Ref** Class-vs-lib refactor plan: lib returns `df`; classes (`SmileResult`/`ForecastResult`)
      wrap — incremental migration order.

## Layer B — demand-driven planner (later; A must not block it)
- [ ] **B1** Subject-of-analysis model (the alpha-search entry point).
- [ ] **B2** Backward-derivation algorithm (goal → data envelope + params) + cycle detection.
- [ ] **B4** Assembler: explicit vs derived; eager/lazy; shared-node caching across runs (sweeps).
- [ ] **B5** Structure / legs + aggregation node; cross-leg coupling representation (correlation/copula).
- [ ] **B6** Data envelope / context entity: what it is; load-once-and-share.

## Cross-cutting
- [ ] **X1** Multi-domain concretely: how `spot` / `bonds` register producers; neutral vs domain kinds.
- [ ] **X2** Portfolio split detail: neutral distributional aggregation vs options payoff aggregation.
- [ ] **X3** Serialization / persistence of results across runs (the R4 *revisit-if* for a light
      self-describing export envelope).
- [ ] **X4** D2 verification plan for the new schemas (Type C where math) — what gets a ledger row.
- [ ] **X5** Consolidation pass: cross-check coherence README ↔ flow-module ↔ structure-requirements ↔
      rejected-branches, then fold the locked decisions into ADR 0003.

## First vertical slice (design → then hand to implementation)
- [ ] **V1** Price slice contract, fully specced: `price_series (timestamp|price) →
      forecast_distribution (quantile|value|change) + scalars{as_of,spot,horizon_years}` — the
      registry entry, the schema, `to_interchange()`, and `price_series` as a registered producer.
      *(Closes enough of A2a/A4a/Sh1 on one concrete path before generalizing.)*
