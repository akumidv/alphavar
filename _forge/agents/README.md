# `_forge/agents/` — alphavar's development agents

Concrete agents that develop **this** project. Each inherits a cross-project **role**
from keystone ([`../keystone/roles/`](../keystone/roles/)) and adds only alphavar
specifics — which modules, docs, tests, and profiles it works with.

> Role = the definition (in keystone, shared). Agent = the incarnation (here, local).
> See the model in [`../keystone/README.md`](../keystone/README.md) §3.

## Roster

| Agent | Inherits role | Works on |
|---|---|---|
| [architect](architect/README.md) | [keystone/roles/architect](../keystone/roles/architect.md) | `docs/dev/` (R#), architecture, the column dictionary, ADRs in `docs/dev/decisions/` |
| [engineer](engineer/README.md) | [keystone/roles/engineer](../keystone/roles/engineer.md) | `src/alphavar/`, `tests/`, the `_forge/tools/` build tools |

## Applied baseline (alphavar)

- **Project type:** `package` (a Python library; will split into packages later) →
  USAGE = root `skills/` for the public API, **no USAGE `tools/`**.
- **Language guardrails (automatic):** [`_common`](../keystone/guardrails/_common.md) +
  [`python`](../keystone/guardrails/python.md).
- **Profiles (opted in):** [`quant`](../keystone/profiles/quant.md) — numerics
  (pricing, smiles, risk).
- **Single backlog:** [`../TASKS.md`](../TASKS.md). Project requirements: R# in
  [`docs/dev/ARCHITECTURE_REQUIREMENTS.md`](../../docs/dev/ARCHITECTURE_REQUIREMENTS.md),
  D# in [`docs/dev/DEVELOPMENT_REQUIREMENTS.md`](../DEVELOPMENT_REQUIREMENTS.md).

## Adding an agent

Add a folder here only when a new role applies, or when one role needs more than one
incarnation in alphavar (e.g. a second `engineer` for a distinct subsystem). Otherwise
extend an existing charter or add a local skill.
