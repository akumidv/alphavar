"""Migrate legacy parquet to the current dictionary (R4.1.1 / R4.2 / R4.5).

The **engine** + the **domain-neutral** spec. It rewrites three things on stored data so it
matches the current registry:

1. **Column names** — legacy → canonical (`kind`→`instrument_kind`, `exchange_*`→`exch_*`,
   identity split `symbol`→`asset_code` / `exchange_symbol`→`exch_symbol`,
   `original_timestamp`→`exch_timestamp`).
2. **Raw prefix → suffix** — `source_<col>` → `<col>_raw` (R4.2 group 3).
3. **Categorical VALUES** — old short codes → readable singular values
   (`kind` `o`/`f`/`s` → `instrument_kind` `option`/`future`/`spot`), per R4.5.

A :class:`MigrationSpec` bundles the renames / value-maps / timestamp-coercion columns. Core
carries only the **neutral** spec (``CORE_SPEC`` — identity, kind, the venue price, timestamps).
Domain-specific legacy mappings (derivatives: `exchange_iv`, `option_type`, the underlying link,
expiration dates) live with that domain and are passed in via ``spec`` — e.g.
``alphavar.options.migration`` merges its domain spec onto ``CORE_SPEC`` so core never has to
describe one domain's columns (R0 / R1).

Idempotent: already-migrated columns/values are left untouched. Neutral CLI at the bottom; the
**full** (domain-aware) conversion runs via the domain wrapper, driven by the
`migrate-stored-data` skill / `data_migration` tool.

    python -m alphavar.core.migration.legacy_parquet /path/to/data --apply   # neutral columns only
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field

import pandas as pd

from alphavar.core.dictionary import Term

_SOURCE_PREFIX = "source_"
_RAW_SUFFIX = "_raw"


@dataclass(frozen=True)
class MigrationSpec:
    """A migration vocabulary: legacy→canonical renames, value remaps, timestamp-coercion cols.

    Domains extend the neutral core spec with ``CORE_SPEC.merged(domain_spec)``; the engine
    functions take a spec and apply it, so core stays domain-neutral."""

    renames: dict[str, str] = field(default_factory=dict)
    value_maps: dict[str, dict[str, str]] = field(default_factory=dict)
    timestamp_cols: tuple[str, ...] = ()

    def merged(self, other: MigrationSpec) -> MigrationSpec:
        """This spec extended by ``other`` (other's entries win on a key clash)."""
        return MigrationSpec(
            renames={**self.renames, **other.renames},
            value_maps={**self.value_maps, **other.value_maps},
            timestamp_cols=tuple(dict.fromkeys((*self.timestamp_cols, *other.timestamp_cols))),
        )


# --- Domain-neutral spec: only concepts shared by every domain (identity / kind / price / time).
CORE_SPEC = MigrationSpec(
    renames={
        # identity (two-level model, R4.1.1)
        "symbol": Term.ASSET_CODE,  # 'BTC' -> asset_code
        "exchange_symbol": Term.EXCH_SYMBOL,  # 'BTC-...-C' -> exch_symbol
        # classification (R4.5)
        "kind": Term.INSTRUMENT_KIND,  # 'o'/'f'/'s' -> instrument_kind
        "asset_type": Term.INSTRUMENT_KIND,  # later-stage name, same concept
        # price + timestamp (R4.2)
        "exchange_price": Term.EXCH_PRICE,
        "original_timestamp": Term.EXCH_TIMESTAMP,
    },
    value_maps={
        Term.INSTRUMENT_KIND: {
            "o": "option",
            "f": "future",
            "s": "spot",
            # already-plural legacy words -> singular
            "options": "option",
            "futures": "future",
        },
    },
    # Datetime columns coerced to a uniform tz-aware (UTC) dtype after migration (legacy files
    # stored these as epoch ints / naive dates / tz-aware, which breaks date-key joins).
    timestamp_cols=(Term.TIMESTAMP, Term.REQUEST_TIMESTAMP, Term.EXCH_TIMESTAMP),
)

# A migrated row must carry at least one identity column. If none is present after migration,
# the file predates any structure this migrator understands -> error.
_IDENTITY_ANY = (Term.ASSET_CODE, Term.BASE_CODE, Term.EXCH_SYMBOL)


class MigrationError(Exception):
    """Raised when a parquet file cannot be safely migrated (old/ambiguous structure or
    type) — surfaced loudly instead of silently producing a half-migrated file."""


def _detect_conflicts(df: pd.DataFrame, spec: MigrationSpec) -> None:
    """Raise if the same canonical concept is present under more than one name — a mixed,
    partially-migrated file we cannot merge unambiguously (e.g. both ``kind`` and
    ``instrument_kind``, or both ``symbol`` and ``asset_code``)."""
    sources_by_target: dict[str, list[str]] = {}
    for old, new in spec.renames.items():
        if old in df.columns:
            sources_by_target.setdefault(new, []).append(old)
    for target, sources in sources_by_target.items():
        present = list(sources)
        if target in df.columns:
            present.append(f"{target} (already canonical)")
        if len(present) > 1:
            raise MigrationError(
                f"ambiguous columns for '{target}': {present} — cannot migrate a "
                f"partially-converted/old-structure file safely"
            )


def _rename_columns(df: pd.DataFrame, spec: MigrationSpec) -> pd.DataFrame:
    renames = {old: new for old, new in spec.renames.items() if old in df.columns and new not in df.columns}
    # source_<col> -> <col>_raw
    for col in list(df.columns):
        if col.startswith(_SOURCE_PREFIX):
            base = col[len(_SOURCE_PREFIX) :]
            # apply the canonical rename to the base too, if any
            base = spec.renames.get(base, base)
            target = f"{base}{_RAW_SUFFIX}"
            if target not in df.columns:
                renames[col] = target
    return df.rename(columns=renames) if renames else df


def _remap_values(df: pd.DataFrame, spec: MigrationSpec) -> pd.DataFrame:
    for col, mapping in spec.value_maps.items():
        if col in df.columns:
            # Only remap recognised old codes; leave already-correct values as-is.
            df[col] = df[col].map(lambda v, m=mapping: m.get(v, v))
    return df


def _coerce_types(df: pd.DataFrame, path: str | None, spec: MigrationSpec) -> pd.DataFrame:
    """Coerce known columns to their canonical dtype; raise MigrationError on unparseable
    legacy types (so a bad/old file fails loudly rather than writing garbage)."""
    for col in spec.timestamp_cols:
        if col in df.columns and not isinstance(df[col].dtype, pd.DatetimeTZDtype):
            try:
                df[col] = pd.to_datetime(df[col], utc=True)
            except (ValueError, TypeError) as err:
                raise MigrationError(
                    f"{path or '<df>'}: column '{col}' is not a parseable timestamp ({df[col].dtype}): {err}"
                ) from err
    return df


def _validate_after(df: pd.DataFrame, path: str | None) -> None:
    if not any(c in df.columns for c in _IDENTITY_ANY):
        raise MigrationError(
            f"{path or '<df>'}: no identity column {list(_IDENTITY_ANY)} after "
            f"migration — unrecognized/too-old structure. Convert manually."
        )


def rename_legacy_columns(df: pd.DataFrame, spec: MigrationSpec = CORE_SPEC) -> pd.DataFrame:
    """Lightweight read-shim (T23.6): rename legacy column names to the current dictionary
    (``original_timestamp`` → ``exch_timestamp``, ``source_<c>`` → ``<c>_raw``, …). **Idempotent**
    — a no-op on an already-current frame. Defaults to the neutral ``CORE_SPEC``; pass a merged
    domain spec to also rename that domain's legacy columns. Value remaps / type coercion stay in
    ``migrate_dataframe``."""
    return _rename_columns(df, spec)


def migrate_dataframe(df: pd.DataFrame, path: str | None = None, spec: MigrationSpec = CORE_SPEC) -> pd.DataFrame:
    """Return a migrated copy of ``df`` (column renames + raw suffix + value remap + type
    coercion) under ``spec``. Raises :class:`MigrationError` on an ambiguous/too-old structure."""
    _detect_conflicts(df, spec)
    df = _rename_columns(df.copy(), spec)
    df = _remap_values(df, spec)
    df = _coerce_types(df, path, spec)
    _validate_after(df, path)
    return df


def migrate_parquet_file(path: str, *, apply: bool, backup: bool = True, spec: MigrationSpec = CORE_SPEC) -> bool:
    """Migrate one parquet file in place. Returns True if anything changed.

    ``apply=False`` is a dry run (reports intended changes, writes nothing).
    """
    df = pd.read_parquet(path)
    migrated = migrate_dataframe(df, path=path, spec=spec)
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


def migrate_parquet_tree(root: str, *, apply: bool, backup: bool = True, spec: MigrationSpec = CORE_SPEC) -> int:
    """Migrate every ``*.parquet`` under ``root`` with ``spec``. Returns count of changed files.

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
                    if migrate_parquet_file(full, apply=apply, backup=backup, spec=spec):
                        count += 1
                except MigrationError as err:
                    failures.append(str(err))
    if failures:
        listed = "\n  - ".join(failures)
        raise MigrationError(
            f"{len(failures)} file(s) could not be migrated automatically (convert these manually):\n  - {listed}"
        )
    return count


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy parquet to the current dictionary (neutral columns).")
    parser.add_argument("root", help="Data root (walked recursively for *.parquet).")
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry run).")
    parser.add_argument("--no-backup", action="store_true", help="Do not keep a .bak copy when applying.")
    args = parser.parse_args(argv)
    n = migrate_parquet_tree(args.root, apply=args.apply, backup=not args.no_backup)
    mode = "migrated" if args.apply else "would migrate"
    print(f"\n{mode} {n} file(s).")
    if not args.apply and n:
        print("Re-run with --apply to write changes (a .bak copy is kept by default).")
    print("Note: this CLI applies only the neutral column spec; domain columns convert via the data_migration tool.")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
