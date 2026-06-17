"""Migrate legacy parquet to the current dictionary (R4.1.1 / R4.2 / R4.5).

This module is the *only* place that knows the project's legacy column names and codes —
the rest of the codebase speaks only the current canonical registry. It brings accumulated
stored data in line with that registry and rewrites three things:

1. **Column names** — legacy → canonical (`kind`→`instrument_kind`, `exchange_*`→`exch_*`,
   identity split `symbol`→`asset_code` / `exchange_symbol`→`exch_symbol`,
   `original_timestamp`→`exch_timestamp`, `option_type`→`option_right`,
   the typo `exhchange_mark_price`→`exch_mark_price`).
2. **Raw prefix → suffix** — `source_<col>` → `<col>_raw` (R4.2 group 3).
3. **Categorical VALUES** — old short codes → readable singular values
   (`option_type` `c`/`p` → `option_right` `call`/`put`; `kind` `o`/`f`/`s` →
   `instrument_kind` `option`/`future`/`spot`), per R4.5 (StrEnum + category, no codes).

Idempotent: already-migrated columns/values are left untouched. Use the CLI at the
bottom or call ``migrate_parquet_tree(root)``.

    python -m alphavar.core.migration.legacy_parquet /path/to/data --apply
"""
from __future__ import annotations
import argparse
import os
import sys
import pandas as pd

from alphavar.core.dictionary import Col

# Some legacy columns map to options-domain names; import lazily-safe constants as plain
# strings to keep this module domain-neutral at import time.
_OPTION_RIGHT = "option_right"

# 1) Column renames: legacy parquet name -> canonical registry name.
COLUMN_RENAMES: dict[str, str] = {
    # identity (two-level model, R4.1.1)
    "symbol": Col.ASSET_CODE,                       # 'BTC' -> asset_code
    "exchange_symbol": Col.EXCH_SYMBOL,             # 'BTC-...-C' -> exch_symbol
    "exchange_underlying_symbol": Col.UNDERLYING_CODE,
    # classification (R4.5)
    "kind": Col.INSTRUMENT_KIND,                    # 'o'/'f'/'s' -> instrument_kind
    "asset_type": Col.INSTRUMENT_KIND,              # later-stage name, same concept
    "option_type": _OPTION_RIGHT,                   # 'c'/'p' -> option_right
    "underlying_asset_type": Col.UNDERLYING_ASSET_CLASS,
    # price/iv + timestamp (R4.2)
    "exchange_price": Col.EXCH_PRICE,
    "exchange_iv": Col.EXCH_IV,
    "exchange_mark_price": Col.EXCH_MARK_PRICE,
    "exhchange_mark_price": Col.EXCH_MARK_PRICE,    # historical double typo
    "exchange_mark_iv": Col.EXCH_MARK_IV,
    "original_timestamp": Col.EXCH_TIMESTAMP,
}

# 2) source_<col> -> <col>_raw is handled programmatically (any source_* column).
_SOURCE_PREFIX = "source_"
_RAW_SUFFIX = "_raw"

# 3) Value maps: canonical column name -> {old code: new readable value}.
VALUE_MAPS: dict[str, dict[str, str]] = {
    Col.INSTRUMENT_KIND: {"o": "option", "f": "future", "s": "spot",
                          # already-plural legacy words -> singular
                          "options": "option", "futures": "future"},
    _OPTION_RIGHT: {"c": "call", "p": "put"},
    Col.UNDERLYING_ASSET_CLASS: {"s": "equity", "share": "equity", "m": "commodity",
                                 "i": "index", "c": "currency", "y": "crypto"},
}

# Datetime columns coerced to a uniform tz-aware (UTC) dtype after migration. Legacy files
# stored these inconsistently (epoch ints, naive `datetime.date`, tz-aware timestamps),
# which breaks joins on date keys (e.g. option.underlying_expiration_date vs
# future.expiration_date). Normalizing to datetime64[UTC] makes them mergeable.
_TIMESTAMP_COLS = (Col.TIMESTAMP, Col.REQUEST_TIMESTAMP, Col.EXCH_TIMESTAMP,
                   Col.EXPIRATION_DATE, Col.UNDERLYING_EXPIRATION_DATE)

# A migrated row must carry at least one identity column. If none is present after
# migration, the file predates any structure this migrator understands -> error.
_IDENTITY_ANY = (Col.ASSET_CODE, Col.BASE_CODE, Col.EXCH_SYMBOL)


class MigrationError(Exception):
    """Raised when a parquet file cannot be safely migrated (old/ambiguous structure or
    type) — surfaced loudly instead of silently producing a half-migrated file."""


def _detect_conflicts(df: pd.DataFrame) -> None:
    """Raise if the same canonical concept is present under more than one name — a mixed,
    partially-migrated file we cannot merge unambiguously (e.g. both ``kind`` and
    ``instrument_kind``, or both ``symbol`` and ``asset_code``)."""
    sources_by_target: dict[str, list[str]] = {}
    for old, new in COLUMN_RENAMES.items():
        if old in df.columns:
            sources_by_target.setdefault(new, []).append(old)
    for target, sources in sources_by_target.items():
        present = list(sources)
        if target in df.columns:
            present.append(f"{target} (already canonical)")
        if len(present) > 1:
            raise MigrationError(
                f"ambiguous columns for '{target}': {present} — cannot migrate a "
                f"partially-converted/old-structure file safely")


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    renames = {old: new for old, new in COLUMN_RENAMES.items()
               if old in df.columns and new not in df.columns}
    # source_<col> -> <col>_raw
    for col in list(df.columns):
        if col.startswith(_SOURCE_PREFIX):
            base = col[len(_SOURCE_PREFIX):]
            # apply the canonical rename to the base too, if any
            base = COLUMN_RENAMES.get(base, base)
            target = f"{base}{_RAW_SUFFIX}"
            if target not in df.columns:
                renames[col] = target
    return df.rename(columns=renames) if renames else df


def _remap_values(df: pd.DataFrame) -> pd.DataFrame:
    for col, mapping in VALUE_MAPS.items():
        if col in df.columns:
            # Only remap recognised old codes; leave already-correct values as-is.
            df[col] = df[col].map(lambda v, m=mapping: m.get(v, v))
    return df


def _coerce_types(df: pd.DataFrame, path: str | None) -> pd.DataFrame:
    """Coerce known columns to their canonical dtype; raise MigrationError on unparseable
    legacy types (so a bad/old file fails loudly rather than writing garbage)."""
    for col in _TIMESTAMP_COLS:
        if col in df.columns and not isinstance(df[col].dtype, pd.DatetimeTZDtype):
            try:
                df[col] = pd.to_datetime(df[col], utc=True)
            except (ValueError, TypeError) as err:
                raise MigrationError(f"{path or '<df>'}: column '{col}' is not a parseable "
                                     f"timestamp ({df[col].dtype}): {err}") from err
    return df


def _validate_after(df: pd.DataFrame, path: str | None) -> None:
    if not any(c in df.columns for c in _IDENTITY_ANY):
        raise MigrationError(f"{path or '<df>'}: no identity column {list(_IDENTITY_ANY)} after "
                             f"migration — unrecognized/too-old structure. Convert manually.")


def migrate_dataframe(df: pd.DataFrame, path: str | None = None) -> pd.DataFrame:
    """Return a migrated copy of ``df`` (column renames + raw suffix + value remap + type
    coercion). Raises :class:`MigrationError` on an ambiguous/too-old structure."""
    _detect_conflicts(df)
    df = _rename_columns(df.copy())
    df = _remap_values(df)
    df = _coerce_types(df, path)
    _validate_after(df, path)
    return df


def migrate_parquet_file(path: str, *, apply: bool, backup: bool = True) -> bool:
    """Migrate one parquet file in place. Returns True if anything changed.

    ``apply=False`` is a dry run (reports intended changes, writes nothing).
    """
    df = pd.read_parquet(path)
    migrated = migrate_dataframe(df, path=path)
    changed = list(migrated.columns) != list(df.columns) or not migrated.equals(df)
    if not changed:
        return False
    added = set(migrated.columns) - set(df.columns)
    removed = set(df.columns) - set(migrated.columns)
    print(f"[{'APPLY' if apply else 'DRY'}] {path}")
    if removed or added:
        print(f"    columns: -{sorted(removed)} +{sorted(added)}")
    if apply:
        if backup and not os.path.exists(path + ".bak"):
            os.rename(path, path + ".bak")
            migrated.to_parquet(path)
        else:
            migrated.to_parquet(path)
    return True


def migrate_parquet_tree(root: str, *, apply: bool, backup: bool = True) -> int:
    """Migrate every ``*.parquet`` under ``root``. Returns count of changed files.

    Files with an old/ambiguous structure are collected and reported together: the good
    files still migrate, then a single :class:`MigrationError` is raised listing every file
    that must be converted manually (the user's one-time local op)."""
    count = 0
    failures: list[str] = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if fn.endswith(".parquet") and not fn.endswith(".bak"):
                full = os.path.join(dirpath, fn)
                try:
                    if migrate_parquet_file(full, apply=apply, backup=backup):
                        count += 1
                except MigrationError as err:
                    failures.append(str(err))
    if failures:
        listed = "\n  - ".join(failures)
        raise MigrationError(f"{len(failures)} file(s) could not be migrated automatically "
                             f"(convert these manually):\n  - {listed}")
    return count


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy parquet to the current dictionary.")
    parser.add_argument("root", help="Data root (walked recursively for *.parquet).")
    parser.add_argument("--apply", action="store_true",
                        help="Write changes (default: dry run).")
    parser.add_argument("--no-backup", action="store_true",
                        help="Do not keep a .bak copy when applying.")
    args = parser.parse_args(argv)
    n = migrate_parquet_tree(args.root, apply=args.apply, backup=not args.no_backup)
    mode = "migrated" if args.apply else "would migrate"
    print(f"\n{mode} {n} file(s).")
    if not args.apply and n:
        print("Re-run with --apply to write changes (a .bak copy is kept by default).")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
