# Memory index

Durable, LLM-agnostic notes. One file per fact/decision. Promote stable items into
`AGENTS.md` / `ARCHITECTURE_REQUIREMENTS.md` and link back here.

- [owner-verifies-math-and-architecture.md](owner-verifies-math-and-architecture.md) —
  DataFrame/quant-math/architecture changes need explanation + explicit owner
  verification; never "done" until verified (codified as D2).
- [env-and-test-running.md](env-and-test-running.md) — uv + Python 3.14, pyarrow<25 for
  cp314 wheels, tests need `--extra etl` + DATA_PATH, `.tmp/` outputs.
- [agent-modes-and-layout.md](agent-modes-and-layout.md) — build (`_dev/`) vs operate
  (`desk/`) split, default=desk modes, and the R#/D#/G# axes placed by subject.
- [agent-artifacts-layout.md](agent-artifacts-layout.md) — why `agents/` lives at the repo
  root (not `docs/`); spec+code together per the Agent Skills standard.
