# Memory index

Durable, LLM-agnostic notes. One file per fact/decision. Promote stable items into
`AGENTS.md` / `ARCHITECTURE_REQUIREMENTS.md` and link back here.

- [owner-verifies-math-and-architecture.md](owner-verifies-math-and-architecture.md) —
  DataFrame/quant-math/architecture changes need explanation + explicit owner
  verification; never "done" until verified (codified as D2).
- [owner-owns-commits.md](owner-owns-commits.md) — the agent never makes landing commits on
  its own (backup branches ok; push/main/PR on request); codified as D5, enforced by the
  `git-commit-guard` PreToolUse hook.
- [env-and-test-running.md](env-and-test-running.md) — uv + Python 3.14, pyarrow<25 for
  cp314 wheels, tests need `--extra etl` + DATA_PATH, `.tmp/` outputs.

> The "agent modes/layout" and "artifacts at repo root" decisions are superseded by the
> **keystone** model — see [`../keystone/README.md`](../keystone/README.md) (the three
> axes, the `_forge/` layout). Dev-assist artifacts live at the repo root (`_forge/`, root
> `skills/`), spec + code together per the Agent Skills standard.
