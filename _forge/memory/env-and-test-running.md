# Environment & test-running gotchas

The `alphavar` package was migrated from Poetry to **uv + hatchling** (2026-06-14),
targeting **Python 3.14**.

Non-obvious operational facts:
- `pyarrow` is pinned `>=21,<25` because Python 3.14 needs cp314 wheels — pyarrow 21 has
  none and falls back to a cmake source build; 24.0.0 ships the wheel. Bump the cap,
  don't install cmake.
- ETL (`alphavar.options.etl`) needs the optional `apscheduler` (extra `etl`). `uv run
  pytest` does NOT activate extras by default and prunes apscheduler → run tests with
  **`uv run --extra etl pytest`** (or `uv sync --all-extras` first).
- `DATA_PATH` (market-data root) is read from `test.env` via pytest-dotenv; conftest
  defaults it to the repo-local `data/` symlink. The `data` symlink is git-ignored and
  machine-local. Hermetic committed fixtures are still TODO (TASKS.md T11).
- Test output artefacts (charts) go to project-root `.tmp/` (git-ignored) via the
  `tmp_output_dir` fixture / `ALPHAVAR_TMP_DIR` env var set in `tests/conftest.py`.

Tasks live in the repo at `_forge/TASKS.md`; formal rules in
`../../../docs/dev/ARCHITECTURE_REQUIREMENTS.md`. See
[owner-verifies-math-and-architecture.md](owner-verifies-math-and-architecture.md).
