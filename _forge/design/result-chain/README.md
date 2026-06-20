# Result chain & data-processing pipeline — design concept (hub)

- **Status:** Working design **concept** — co-design in progress (started 2026-06-20). Owner:
  akuminov@gmail.com. **Durable & returnable**: picked up across different sessions / agents. Not a
  settled ADR. Nothing here is built yet.
- **This is iterative.** Walked **several times in a cycle**; expect to revisit. Rejected ideas are
  **not deleted** — they move to [`rejected-branches.md`](rejected-branches.md) *with the reason*,
  because a later pass (different constraints) may revive one. A **consolidated design** pass comes
  after the open points settle.
- **Relates to:** [ADR 0003](../../../docs/dev/decisions/0003-composable-result-chain.md) (composable
  result-chain — this widens its Phase 1 scope), [ADR 0002](../../../docs/dev/decisions/0002-forecast-model-factory-axes.md),
  R0/R3/R4/R5, D2. Backlog: T27 (forecast factor-conditional), T33 (portfolio), T35 (risk), T30.

## Files in this concept

- **`README.md`** (this hub) — vision, the DAG, the two layers, the resulting shape, the **open-point
  index**. Start here.
- **[`flow-module.md`](flow-module.md)** — **Layer A** (the `alphavar.flow` package): the mechanical
  structure & exchange. Result = frame + scalars, the I/O **contract**, registry, resolver,
  multi-domain, naming. (Build-now layer.)
- **[`structure-requirements.md`](structure-requirements.md)** — **Layer B** (demand-driven planner):
  subject-of-analysis, backward derivation, the `Plan`, multi-leg structures + aggregation, the data
  envelope. (Later layer; A must not block it.)
- **[`rejected-branches.md`](rejected-branches.md)** — dead-ends & rejected hypotheses, each with
  *why* and a *revisit-if* condition.
- **[`TASKS.md`](TASKS.md)** — the **design backlog** (separate from the implementation backlog
  `agents/_dev/TASKS.md`): each task = a design decision to make, not code.

## Goal

Calculations are not dead-ends — the output of one feeds the next (a fit feeds a forecast; a forecast
feeds VaR/CVaR; a factor-conditional price model needs another forecast as its factor scenario). We
want a **single, end-to-end contract** so that, from data loading onward, every step's **inputs and
outputs are described in one shared vocabulary** — making the entities **compatible / composable**.

The compatibility lives in the **descriptions (contracts/schemas)**, *not* inside any one orchestrator
— so a chain can be assembled **either** by `flow` (auto, demand-driven) **or** by a user in plain
code. The domain implementations (`core`/`io`/`options`/`spot`/`portfolio`/`risk`) **know nothing
about `flow`**; they do their narrow task and expose a described contract.

**The pipeline is broader than forecast, and it branches** — a **DAG we assemble**, not a line:

```
            ┌─────────────────────────────────────────────────────────────┐
            │   DATA ENVELOPE  — NOT just the legs.                         │
            │   the full board over a day / period: every strike &          │
            │   expiration, the underlying/futures, history — because       │
            │   fit / fill / forecast need richer context than the legs.    │
            └───────────────────────────┬─────────────────────────────────┘
                                        │  load
                                        ▼
                                    validate
                                        │
                                      clean
                                        │
                                  fit smiles  ──►  fill missing K/expiry via surface
                                        │                 (board-level, shared node)
                  ┌─────────────────────┼─────────────────────┐   fan-out: per leg
                  ▼                     ▼                     ▼
               leg A                 leg B                 leg C
            forecast/price        forecast/vol         forecast/surface
                  └─────────────────────┼─────────────────────┘
                                        ▼   fan-in: COLLECTIVE (correlation / copula)
                                   aggregate (structure)
                                        │
                            ┌───────────┴───────────┐
                            ▼                       ▼
                       risk (VaR/CVaR)        other leaf (P&L, …)
```

Shared nodes (the cleaned/filled board) are consumed by every leg and by the aggregate → a DAG, run
once and reused, not recomputed per branch.

### Two axes of branching

1. **Vertical (per instrument): the calc chain** — load → validate → clean → fit → fill → forecast /
   risk / portfolio.
2. **Horizontal (across legs): a structure of several legs** — assemble N legs and run the chain over
   the structure **collectively**: per-leg **fan-out** + a **collective fan-in** (portfolio VaR/CVaR
   over the *correlated* leg distributions — not a naive sum). Detail in
   [`structure-requirements.md`](structure-requirements.md).

## Two layers (design & build them separately)

- **Layer A — structure & chain-exchange** (mechanical, forward, data-driven): producers, the
  `Result`, the I/O **contract**, the registry, the resolver. *The plumbing.* → [`flow-module.md`](flow-module.md).
- **Layer B — assembly / planning** (goal-driven, backward, demand-driven): the **alpha-search**
  heart — think in terms of the *subject of analysis*, not the data you happen to have. Walks the goal
  backward to the **data envelope + parameters**. → [`structure-requirements.md`](structure-requirements.md).

`flow` is **one** assembler of Layer A, not privileged; a user can assemble by hand. The **`Plan`** is
the interface between B (builds it) and A (executes it).

## Resulting shape (post-pivot)

```
3 tiers (each usable alone, depend only downward):
  lib    : pure functions, df + params → df          # Shape 1: df+cols / Series · Shape 2: new tidy frame
  class  : df → ergonomic object + recomputed scalars (as_of/spot) + bound eval funcs   # in-process exchange
  flow   : contracts, Registry, Plan, resolver        # on top; non-privileged

Two shapes of a lib function (test: one output per input row?):
  Shape 1 enrichment (row-aligned)  → df + column(s) / Series ;  compat = column presence (OPTION_COLUMN_DEPENDENCIES)
  Shape 2 reduction  (new axis)     → new tidy frame of a kind ;  compat = kind / frame-schema (the contract)
  → a new entity-frame (PnL, var, forecast, surface, smile-fit) = a new Shape-2 kind/schema.

Contract  : kind → (input kinds + param-spec, output frame-schema + scalar-spec)   # basis of compatibility
Registry  : kind → Contract            # PYTHON code in flow (binds functions + pandera schemas; type-safe)
Plan      : the chain as DATA (kinds + edges + params)   # YAML / dict — human & AI authorable; flow interprets
Structure : [leg, …] + aggregation node                  # multi-leg collective unit (Layer B)
Resolver  : reads Registry, executes the Plan forward, caches shared nodes   (flow, Layer A)
RunRecord : provenance/lineage of a run                  # owned by flow, optional; NOT threaded on results
```

> **Pivot (owner, 2026-06-20):** there is **no `ResultMeta` provenance entity** on results. What it
> would have held is either (a) scalar *values* — already described by the contract and carried as the
> ergonomic object's fields / function returns, or (b) provenance — which is `flow`'s `RunRecord`, not
> a domain concern. See [`rejected-branches.md`](rejected-branches.md) R4 and
> [`flow-module.md`](flow-module.md) "Data vs contract".

## Open-point index

Detail (with leanings/decisions) lives in the layer files. Status: *decided* / *under discussion* /
*pending*.

**Layer A** ([`flow-module.md`](flow-module.md)):
- **A0** Module name & home — *DECIDED: `alphavar.flow`* (+ `composer` inside).
- **A1** `ResultMeta` shared type? — *RESOLVED by removal* (no meta entity; contract describes scalars).
- **A2** How formal is the contract/registry — *decided: Registry = Python code in flow* (binds
  functions + pandera schemas; type-safe). Open: param-spec format & acyclicity checking.
- **A9** Layering (lib functional / class / flow) + **two shapes** of a lib function (Shape 1
  enrichment via column-deps; Shape 2 new-kind frame) — *principle, accepted*.
- **A3** Lineage refs vs embed — *COLLAPSED into `flow.RunRecord`* (no lineage on results).
- **A4** Interchange frame form — *leaning tidy* (+ keep wide `to_frame()` as ergonomic render).
- **A5** Where neutral terms live — *pending* (`core.dictionary`, new registry vs extend `Term`).
- **A6** Input-contract expressiveness ("board over period P") — *pending*.
- **A7** `flow` non-privileged; external/manual assembly works off the contract — *principle, accepted*.
- **A8** A `kind` is a contract, **not** forced decomposition — consolidated producers stay, reuse at
  the lib level, intermediate interchange is opt-in (efficiency) — *principle, accepted*.

**Invocation** is not necessarily dotted: a producer can be called via the facade (`.method()`), as a
plain function, or **declaratively** as a `Plan` (a "transformation model" — the chain as data) that
`flow` interprets. Same contract for all three. See [`flow-module.md`](flow-module.md).

**Current focus / next:** prototype the contract on the **price vertical slice** (`price_series →
forecast_distribution`) — it is ~90% there (needs only `to_interchange()` + a pandera schema +
registering `price_series`). No behavior change to the existing facade. See the gap analysis &
examples in [`flow-module.md`](flow-module.md).

**Layer B** ([`structure-requirements.md`](structure-requirements.md)):
- **B1** Subject-of-analysis model — *pending*.
- **B2** Backward derivation (goal → envelope + params) — *pending*.
- **B3** `Plan` as the A/B interface — *pending*.
- **B4** Assembler explicit vs derived; eager/lazy; shared-node caching — *pending*.
- **B5** Structure / legs + aggregation node — *pending*.
- **B6** Data envelope / context entity — *pending*.
