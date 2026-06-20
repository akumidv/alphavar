"""Options/futures domain migration: the derivatives legacy-column spec + domain-aware wrappers.

Core (`alphavar.core.migration`) owns the neutral engine + ``CORE_SPEC``. This module adds the
**derivatives** legacy mappings core must not know about (the underlying link, implied vol, mark,
the `option_type`→`option_right` rename and its value codes, expiration dates), merged onto the
core spec as ``OPTIONS_SPEC``. The wrappers below are the full (domain-aware) conversion used by
the `data_migration` tool and the `migrate-stored-data` skill.
"""

from alphavar.core.migration import CORE_SPEC, MigrationSpec, migrate_parquet_tree, rename_legacy_columns
from alphavar.options.dictionary import OptionsTerm

_OPTION_RIGHT = OptionsTerm.OPTION_RIGHT

# Derivatives-only legacy mappings (kept out of core so core never describes a domain's columns).
OPTIONS_MIGRATION_SPEC = MigrationSpec(
    renames={
        "exchange_underlying_symbol": OptionsTerm.UNDERLYING_CODE,
        "option_type": _OPTION_RIGHT,  # 'c'/'p' -> option_right
        "underlying_asset_type": OptionsTerm.UNDERLYING_ASSET_CLASS,
        "exchange_iv": OptionsTerm.EXCH_IV,
        "exchange_mark_price": OptionsTerm.EXCH_MARK_PRICE,
        "exhchange_mark_price": OptionsTerm.EXCH_MARK_PRICE,  # historical double typo
        "exchange_mark_iv": OptionsTerm.EXCH_MARK_IV,
    },
    value_maps={
        _OPTION_RIGHT: {"c": "call", "p": "put"},
        OptionsTerm.UNDERLYING_ASSET_CLASS: {
            "s": "equity",
            "share": "equity",
            "m": "commodity",
            "i": "index",
            "c": "currency",
            "y": "crypto",
        },
    },
    timestamp_cols=(OptionsTerm.EXPIRATION_DATE, OptionsTerm.UNDERLYING_EXPIRATION_DATE),
)

# The full spec for options/futures data: neutral core + the derivatives mappings.
OPTIONS_SPEC = CORE_SPEC.merged(OPTIONS_MIGRATION_SPEC)


def rename_legacy_option_columns(df):
    """Read-shim with the full (core + derivatives) column renames, for loading legacy options."""
    return rename_legacy_columns(df, OPTIONS_SPEC)


def migrate_options_parquet_tree(root: str, *, apply: bool, backup: bool = True) -> int:
    """Column-convert every parquet under ``root`` with the full options spec (history or updates)."""
    return migrate_parquet_tree(root, apply=apply, backup=backup, spec=OPTIONS_SPEC)
