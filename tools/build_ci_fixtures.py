"""Build a small, committed parquet fixture set for hermetic CI (T11).

The full local data tree (``$DATA_PATH`` or ``./data``, gitignored, ~11 MB) is trimmed into
``tests/fixtures/data/`` (committed, ~1 MB) so the suite is green on a clean checkout with no
local data. ``tests/conftest.py`` defaults ``DATA_PATH`` to that committed set; point
``DATA_PATH`` at the full tree for richer local runs.

What it keeps (verified to keep the suite green):
- option EOD history: the last ``--option-timestamps`` settlement days (full chains);
- future EOD history: whole (already tiny);
- update snapshots: the first ``--update-files`` files per kind, structure preserved.

Run from the repo root:  ``uv run python -m tools.build_ci_fixtures``
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil

import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(REPO_ROOT, "tests", "fixtures", "data")
UPDATE_KINDS = ("future", "future_combo", "option", "option_combo")


def _src_root() -> str:
    src = os.environ.get("DATA_PATH") or os.path.join(REPO_ROOT, "data")
    if not os.path.isdir(src):
        raise SystemExit(f"source data not found: {src} (set DATA_PATH to the full tree)")
    return os.path.abspath(src)


def build(option_timestamps: int, update_files: int) -> None:
    src = _src_root()
    shutil.rmtree(DST, ignore_errors=True)

    # option EOD — keep the last N settlement timestamps (full rows), recompress zstd.
    opt_rel = "DERIBIT/BTC/option/EOD/2025.parquet"
    opt = pd.read_parquet(os.path.join(src, opt_rel))
    keep = sorted(opt["timestamp"].unique())[-option_timestamps:]
    opt = opt[opt["timestamp"].isin(keep)].reset_index(drop=True)
    os.makedirs(os.path.join(DST, os.path.dirname(opt_rel)), exist_ok=True)
    opt.to_parquet(os.path.join(DST, opt_rel), compression="zstd")

    # future EOD — whole (already tiny).
    fut_rel = "DERIBIT/BTC/future/EOD/2025.parquet"
    os.makedirs(os.path.join(DST, os.path.dirname(fut_rel)), exist_ok=True)
    pd.read_parquet(os.path.join(src, fut_rel)).to_parquet(os.path.join(DST, fut_rel), compression="zstd")

    # update snapshots — first K files per kind, structure preserved, recompressed.
    n_update = 0
    for kind in UPDATE_KINDS:
        files = sorted(
            glob.glob(os.path.join(src, "update", "DERIBIT", "BTC", kind, "**", "*.parquet"), recursive=True)
        )[:update_files]
        for path in files:
            rel = os.path.relpath(path, src)
            os.makedirs(os.path.join(DST, os.path.dirname(rel)), exist_ok=True)
            pd.read_parquet(path).to_parquet(os.path.join(DST, rel), compression="zstd")
            n_update += 1

    print(
        f"fixtures -> {os.path.relpath(DST, REPO_ROOT)}: option {len(opt)} rows "
        f"({len(keep)} days), future EOD, {n_update} update files"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--option-timestamps", type=int, default=3)
    parser.add_argument("--update-files", type=int, default=8)
    args = parser.parse_args()
    build(args.option_timestamps, args.update_files)


if __name__ == "__main__":
    main()
