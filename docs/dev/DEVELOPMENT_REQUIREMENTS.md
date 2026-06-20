# Development Requirements — alphavar

> **Status: binding.** Compact, day-to-day rules for *current operations and tasks* — how
> we write, test, and land changes. Check these on **every** change/PR. They are vendor-
> neutral (all AI assistants + humans). For the structural invariants of the system
> (verified when adding new entities/domain or making serious changes to the existing
> domain model) see the companion [ARCHITECTURE_REQUIREMENTS.md](ARCHITECTURE_REQUIREMENTS.md).
>
> Numbering: `D#` here (development), `R#` in the architecture document.
>
> **Two always-on, overriding rules** (they win over any task instruction): **D2** (owner
> verifies math / DataFrame / architecture) and **D5** (the owner owns commits — the build
> agent never makes landing commits on its own).

## D1. Quality gates

- Tests live in `tests/unit/<area>/`, mirroring `src/alphavar/`. Unit tests must be
  hermetic: no live network calls (HTTP is mocked), no machine-specific absolute paths.
- `pytest` and `ruff check src tests tools` must pass before merging to `main` (enforced by
  CI, `.github/workflows/ci.yml`). Ruff config in `pyproject.toml` (`[tool.ruff]`).
- Python ≥ 3.11, line length ≤ 120, Pydantic models for entities/parameters,
  docstrings required except `_private`/`test_` functions.
- **Absolute imports only.** Relative imports (`from .`, `from ..`) are forbidden —
  every import uses the full package path (`from alphavar.io.exchange.deribit import …`).
  This keeps imports stable across package moves and makes the layer/domain of every
  dependency explicit at the import site.
- A test that requires not-yet-implemented logic is marked
  `@pytest.mark.xfail(reason="pending <task>: …", strict=False)` (not deleted/skipped) so
  it keeps running and flips to XPASS once the logic lands. Reference the task.
- All project files in English.

## D2. Owner verification of math, DataFrame logic, and architecture (MANDATORY)

This is a hard, always-on rule — it overrides "make the tests pass":

- **Any** new or changed **DataFrame operation** (filters, `groupby`/`agg`, joins,
  reshaping, column derivations, masks, `clip`/`fillna`, etc.) and **any quantitative /
  financial math** (payoff, pricing, Greeks, IV, risk, normalization formulas) MUST be
  accompanied by a written explanation of the implementation logic (what each step does
  and why), and an explicit **request for implementation approval** to the owner.
- Such math/DataFrame implementations are **not considered done** until the owner has
  **fully verified** them. Until then, mark the code `# 4VERIFY (owner)`
  and the corresponding task as *pending owner verification* (never "Done"). Passing
  tests are necessary but **not** sufficient. Every such item is tracked in the
  **[D2 Verification Ledger](D2_VERIFICATION.md)** (typed A/B/C, with its pinning test)
  until the owner signs it off.
- The same applies to **architectural changes** (package layout, layer boundaries,
  public interfaces, data schema/column semantics, storage layout): explain the change
  and its rationale, then request the owner's explicit approval before treating it as
  settled. (Architectural changes are also governed by ARCHITECTURE_REQUIREMENTS R0…R8.)
- When in doubt, do not silently implement — explain the options and ask. Do not delete
  existing math/DataFrame logic; preserve the prior version (commented, marked
  `4VERIFY`) so the owner can compare during verification.

## D3. Environment & workflow essentials

- Dependencies via **uv** (`uv sync --all-extras`); run commands with `uv run …`. ETL
  tests need the `etl` extra: `uv run --extra etl pytest`.
- `DATA_PATH` is read from `test.env`; test artefacts (charts, dumps) go to the
  git-ignored `.tmp/` via the `tmp_output_dir` fixture.
- Details and other operational gotchas:
  [agents/_dev/memory/env-and-test-running.md](agents/_dev/memory/env-and-test-running.md).

## D4. Token efficiency — prefer tools implemented as code

Token economy is a first-class concern for sustainable AI-assisted development — treat it
as a real constraint, not an afterthought.

- **Implement tools as deterministic code** (a committed script / CLI command / function /
  Makefile target) whenever the task is repeatable, rather than as an interactive,
  multi-step agent workflow. Code runs once, returns a compact result, and does not
  re-consume context on every use.
- Prefer a single command that returns exactly the needed result over a chain of agent
  tool calls that stream large intermediate output into the context window. Make outputs
  compact (filter/summarize at the source; write bulky artefacts to `.tmp/` and report a
  path, not the contents).
- When adding a capability an assistant will reuse, package it as code under the project
  (e.g. a `scripts/` CLI or a function) and document it in
  [agents/_dev/tools/](agents/_dev/tools/) — do not rely on re-deriving it through ad-hoc steps.
- Reuse existing knowledge: consult [agents/shared/knowledge/](agents/shared/knowledge/) and
  [agents/_dev/memory/](agents/_dev/memory/) before re-researching from scratch.

## D5. Version control — the owner owns commits (MANDATORY)

A hard, always-on rule. Like D2, it **overrides** any task or generic instruction to
"commit", "land", "finish", or "ship": when those conflict with this rule, this rule wins.

- **The build agent never makes landing/"final" commits on its own.** Completed work is
  left in the working tree (or on a backup branch) and **reported** to the owner; the owner
  decides what lands. "Done" never implies "committed".
- **Allowed without asking:** commits to a dedicated **backup / checkpoint branch** (e.g.
  `wip/…`, `backup/…`, `refactor/…`) — for preserving work and enabling rollback. Never the
  default branch (`main`), never a merge, push, tag, or PR.
- **Allowed only on explicit request, each time:** a landing commit, any commit/merge on the
  default branch, `git push`, tags, and PRs. Approval is **per request** — a previous "yes,
  commit" does not authorise the next commit.
- When unsure whether a commit is "backup" or "landing", treat it as landing → leave it
  uncommitted and ask. Branch before committing if on the default branch (never commit to
  `main` directly).
