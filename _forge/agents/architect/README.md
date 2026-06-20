# Agent: alphavar architect

**Inherits** [keystone/roles/architect](../../keystone/roles/architect.md) — that file is
the source of mission, scope, pipeline, requirements, guardrails, and definition of done.
This charter adds **only alphavar specifics**; it does not restate the role.

## What this agent works on (alphavar)

- **Architecture & requirements:** [`docs/dev/ARCHITECTURE_REQUIREMENTS.md`](../../../docs/dev/ARCHITECTURE_REQUIREMENTS.md)
  (**R#** — layering, the provider pattern, the domain model, the column
  dictionary/naming).
- **Decisions (ADRs):** [`docs/dev/decisions/`](../../../docs/dev/decisions/).
- **Design surface in code (verify against, don't trust memory):**
  - `src/alphavar/core/` — dictionary, migration, shared primitives.
  - `src/alphavar/io/` — exchange sources + the provider pattern.
  - `src/alphavar/options/` — the options domain (etl, pricer, smiles, normalization).
- **Verification policy:** [`docs/dev/D2_VERIFICATION.md`](../../../docs/dev/D2_VERIFICATION.md)
  — math/DataFrame/architecture decisions need explicit owner verification.

## Profiles in effect

- [`quant`](../../keystone/profiles/quant.md) — numerics conventions apply to any design
  touching pricing, smiles, Greeks, or risk.

## Pipeline (alphavar specifics over [design-flow](../../keystone/pipelines/design-flow.md))

- **Survey** reads the relevant `src/alphavar/<area>/` before proposing changes — the
  column dictionary and the provider/exchange contracts drift; confirm them in code.
- **Record** writes the ADR into `docs/dev/decisions/` and updates the matching **R#**.
- **Hand off** opens the implementing task in [`../../TASKS.md`](../../TASKS.md) for the
  [engineer](../engineer/README.md) agent, linking the design + R#.

## Hand-off boundary

Produces design + R# + ADR + a task. Does **not** write code/tests — that is the
[engineer](../engineer/README.md) agent.
