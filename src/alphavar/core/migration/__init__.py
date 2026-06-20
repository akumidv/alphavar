"""Data migrations: bring accumulated legacy parquet in line with the current dictionary (R4.x).

Core carries the **neutral** engine + ``CORE_SPEC``; a domain (e.g. ``alphavar.options.migration``)
merges its own :class:`MigrationSpec` onto it.
"""

from alphavar.core.migration.legacy_parquet import (
    CORE_SPEC,
    MigrationError,
    MigrationSpec,
    migrate_dataframe,
    migrate_parquet_file,
    migrate_parquet_tree,
    rename_legacy_columns,
)

__all__ = [
    "migrate_dataframe",
    "migrate_parquet_file",
    "migrate_parquet_tree",
    "rename_legacy_columns",
    "MigrationError",
    "MigrationSpec",
    "CORE_SPEC",
]
