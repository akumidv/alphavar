# Agent: alphavar reviewer

**Inherits** [keystone/roles/reviewer](../../keystone/roles/reviewer.md) —
that file is the source of mission, scope, pipeline, requirements, guardrails, and definition of
done. This charter adds **only alphavar specifics**; it does not restate the role.

## What this agent reviews (alphavar)

- **Architecture requirements:** [`docs/dev/ARCHITECTURE_REQUIREMENTS.md`](../../../docs/dev/ARCHITECTURE_REQUIREMENTS.md)
  (**R#**) and accepted ADRs in [`docs/dev/decisions/`](../../../docs/dev/decisions/).
- **Project overview:** [`docs/dev/PROJECT_OVERVIEW.md`](../../../docs/dev/PROJECT_OVERVIEW.md)
  as the intended map of modules and extension points.
- **Design/backlog context:** [`../../TASKS.md`](../../TASKS.md), especially active architecture
  remediation and domain-roadmap tasks.
- **Code structure to verify against:**
  - `src/alphavar/core/` — domain-neutral dictionary and schema migration primitives.
  - `src/alphavar/io/` — provider/exchange/data-source boundaries, secrets, network and file I/O.
  - `src/alphavar/options/` — options/futures domain model, facade classes, pure `lib/`, schemas,
    ETL, analytics, charting, and normalization.
  - `skills/` — USAGE layer contract for downstream assistants using the public API.

## Review focus

- Review lens: use
  [`architecture-review`](../../keystone/pipelines/architecture-review.md) for architecture/risk/
  trade-off checks; use the draft [`security-review`](../../keystone/pipelines/security-review.md)
  only when the task explicitly has a security lens or touches credentials, network/file/shell,
  publication, generated code, unsafe input, or dependency boundaries.
- Scope detection: infer whether the requested subject is all `alphavar`, one domain such as
  `options`, an infrastructure subsystem such as `io/provider`, a component such as `options/lib`,
  or a specific module/function; state parent context and cross-boundary dependencies first.
- Layer separation: domain-neutral core/io vs `options`, and pure `options/lib` vs stateful
  facade/ETL/I/O code.
- Provider pattern: whether exchange-specific code stays behind provider/exchange abstractions.
- DataFrame contracts: canonical columns, schema validation, mutation/in-place hotspots, and
  migration boundaries.
- Domain model: option/future entities, volatility/smile/surface concepts, forecast/risk concepts,
  and naming consistency across docs, dictionary, schemas, and skills.
- Security and operational safety: `.env` secrets, provider credentials, network/file I/O, notebook
  and demo assumptions, generated artifacts, and release/package reviewability.
- Quant profile: numerics, math-shaping assumptions, and D2 owner-verification load.

## Output routing

- Requirement/ADR/design clarification → [architect](../architect/README.md).
- Code/test/tooling remediation → [engineer](../engineer/README.md).
- Reusable process learning → `_forge/memory/` through the keystone learn loop.
- Release/package notes → keystone [release](../../keystone/roles/release.md) role.
