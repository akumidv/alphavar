# keystone AI-assist model — layers, axes, names

The repo's AI assistance follows the **keystone** standard (a personal, cross-project
baseline, destined to become a product / MCP server). Canonical text lives in
[`../keystone/README.md`](../keystone/README.md); this note is the durable summary.

**Names (decided 2026-06-20):**
- `_forge/` — the project's **dev layer** (meta/non-prod; a real Python package — tools
  import as `_forge.tools.*`). Replaced the old `agents/_dev/` (interim `_ai_dev/`).
- `_forge/keystone/` — the **SHARED cross-project standard**, a git submodule.
- Submodule **repo = `ai_keystone`** (`github.com/akumidv/ai_keystone`), **mount path =
  `_forge/keystone`** (repo name ≠ mount path, wired in `.gitmodules`).

**Three layers (the layer axis — a decision tree, not a grid):** DEVELOP → SHARED
(`_forge/keystone/`) / LOCAL (`_forge/{skills,tools,memory,agents}/`); USE → USAGE (root
`skills/`). There is no "shared usage" cell.

**Three orthogonal axes:** Layer (SHARED/LOCAL/USAGE) · Role (architect/engineer) · Project
type (package/service/mcp/…). See [[keystone-role-vs-agent]] and [[keystone-knowledge-layer]].

**This project:** archetype = `package`, language = python, profile = `quant`.

Editing under `_forge/keystone/**` commits to the `ai_keystone` repo — see
[[keystone-edits-go-to-submodule]].
