"""Migrate a local data store to the singular instrument-kind canon (ADR 0001 / R4.5).

Renames the legacy **plural** kind directories to the canonical **singular** tokens
everywhere under a data root (both the history tree `EXCHANGE/ASSET/<kind>/…` and the
`update/EXCHANGE/ASSET/<kind>/…` tree):

    options  -> option
    futures  -> future
    (spot stays spot)

Console tool (tools/README.md): the owner runs it by hand; an agent may run the same
command. Dry-run by default — pass ``--apply`` to actually rename. Pair it with
``python -m alphavar.core.migration.legacy_parquet <root> --apply`` to expand the parquet
*column* values (`o`/`f`/`s` -> `option`/`future`/`spot`); pass ``--contents`` here to run
that step too.

    uv run python tools/migrate_data_layout.py /path/to/data            # preview
    uv run python tools/migrate_data_layout.py /path/to/data --apply    # rename dirs
"""
from __future__ import annotations
import argparse
import os
import sys

from alphavar.core.dictionary import InstrumentKind
from alphavar.options_lib.dictionary import Timeframe

# Legacy plural dir name -> canonical singular (matches provider._instrument_kind_segment).
RENAME = {
    "options": InstrumentKind.OPTION.value,   # option
    "futures": InstrumentKind.FUTURE.value,   # future
}

# Recognized kind-level tokens AFTER renaming: canonical singular kinds + venue-native combo
# tokens (raw update store). A kind dir with any other token is an old/unknown layout.
KNOWN_KIND_TOKENS = {k.value for k in InstrumentKind} | {"future_combo", "option_combo"}
_TIMEFRAME_NAMES = {tf.value for tf in Timeframe}


class LayoutError(Exception):
    """Raised when the data tree has an old/unrecognized layout that must be converted by hand."""


def validate_layout(root: str) -> None:
    """Raise LayoutError if a kind-level directory uses an unrecognized token (old path
    structure). The kind dir is the *parent* of a timeframe dir (EOD/1m/5m/…), which is a
    reliable anchor regardless of how many exchange/asset levels precede it. Run this AFTER
    the rename, so legacy plural dirs are already singular."""
    bad: set[str] = set()
    for dirpath, dirnames, _ in os.walk(root):
        if os.path.basename(dirpath) in _TIMEFRAME_NAMES:
            kind_dir = os.path.dirname(dirpath)
            token = os.path.basename(kind_dir)
            if token not in KNOWN_KIND_TOKENS and token not in RENAME:
                bad.add(os.path.relpath(kind_dir, root))
    if bad:
        raise LayoutError("unrecognized kind directories (old layout — convert manually):\n  - "
                          + "\n  - ".join(sorted(bad)))


def plan_renames(root: str) -> list[tuple[str, str]]:
    """Bottom-up list of (src_dir, dst_dir) for every legacy kind dir under root."""
    renames: list[tuple[str, str]] = []
    for dirpath, dirnames, _ in os.walk(root, topdown=False):
        for name in dirnames:
            if name in RENAME:
                renames.append((os.path.join(dirpath, name),
                                os.path.join(dirpath, RENAME[name])))
    return renames


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", help="data store root (the DATA_PATH dir)")
    parser.add_argument("--apply", action="store_true", help="perform the rename (default: dry-run)")
    parser.add_argument("--contents", action="store_true",
                        help="also expand parquet column values via legacy_parquet migrator")
    parser.add_argument("--no-validate", action="store_true",
                        help="skip the post-rename layout check (which errors on old/unknown layouts)")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"ERROR: {root} is not a directory", file=sys.stderr)
        return 2

    renames = plan_renames(root)
    if not renames:
        print(f"No legacy plural kind dirs under {root} — already singular.")
    for src, dst in renames:
        rel = os.path.relpath(src, root)
        if os.path.exists(dst):
            print(f"SKIP  {rel}  (target {os.path.basename(dst)} already exists)")
            continue
        print(f"{'RENAME' if args.apply else 'WOULD'}  {rel} -> {os.path.basename(dst)}")
        if args.apply:
            os.rename(src, dst)

    # After renaming, fail loudly on any old/unrecognized kind directory rather than
    # leaving it silently behind (the owner converts those manually).
    if args.apply and not args.no_validate:
        validate_layout(root)

    if args.contents:
        from alphavar.core.migration.legacy_parquet import migrate_parquet_tree
        print(f"\n{'Migrating' if args.apply else 'Would migrate'} parquet column values…")
        n = migrate_parquet_tree(root, apply=args.apply)
        print(f"  {'migrated' if args.apply else 'would migrate'} {n} file(s)")

    if not args.apply:
        print("\nDry-run. Re-run with --apply to perform the changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
