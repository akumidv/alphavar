# Agent artifacts live in root `agents/`, not `docs/`

**Decided 2026-06-14.** AI-assisted-development artifacts (memory, skills, tools,
knowledge) live in a **repo-root `agents/`** directory, moved out of `docs/dev/agents/`.

**Why:** they are agent artifacts, not project documentation — `docs/` is the
user/project-facing audience (it also hosts a Next.js site). Keeping AI tooling in `docs/`
conflated two audiences and forced a split between a tool's *spec* (docs) and its
*executable code* (can't live in docs). Root `agents/` keeps spec + code together, per the
Anthropic **Agent Skills** standard (a skill = a folder with its `SKILL.md` + `scripts/`).

**Layout consequences:**
- `agents/tools/<tool>.md` (spec) + `agents/tools/<tool_pkg>/` (code) sit together.
- Test-only helpers are NOT agent tools → `tests/utils/` (imported by conftest).
- `docs/dev/AI_WORKING_MODEL.md` was merged into `agents/README.md` (the working model
  now lives with the artifacts it describes).
- Pytest `pythonpath` includes `.` so `agents.*` and `tests.utils.*` import as packages.

Full rationale + compared practices (AGENTS.md standard, Agent Skills, repo conventions)
in [agents/README.md](../README.md). This note graduates into AGENTS.md "Documentation
Conventions" (already updated) — kept here as the decision record.
