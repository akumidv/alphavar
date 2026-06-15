# `shared/` — cross-agent substrate

Artifacts used by **both** agent classes (build and desk) — kept here so they are written
once and consumed everywhere. This is the staging ground for what will later be exposed as
an **MCP** server, so the wider ecosystem (other repos, `catcher-bot`, server-side agents)
can query it without copying.

## Contents

- [`knowledge/`](knowledge/) — concentrated, **sourced** domain reference: exchanges & their
  APIs, options theory, risk, portfolio. Every non-trivial fact carries a source so it can
  be re-queried. **Consult before re-researching the domain.** → destined for MCP.

_Shared `skills/` and `tools/` will be added here when a second agent needs the same
playbook/code; until then a skill/tool lives with its owning agent and is promoted to
`shared/` on first reuse (mechanical+repeated → tool; ordering/judgement → skill)._

See the agent operating model and entity theses in [`../README.md`](../README.md).
