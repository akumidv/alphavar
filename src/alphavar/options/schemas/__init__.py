"""Options/futures pandera schemas + boundary validation (R4.4)."""

import os

import pandas as pd

from alphavar.options.schemas._schemas import (
    FuturesHistory,
    GreeksMixin,
    IdentityMixin,
    OHLCMixin,
    OptionsHistory,
    QuoteMixin,
    SpotHistory,
    TimestampMixin,
)

__all__ = [
    "OptionsHistory",
    "FuturesHistory",
    "SpotHistory",
    "IdentityMixin",
    "TimestampMixin",
    "QuoteMixin",
    "OHLCMixin",
    "GreeksMixin",
    "validate",
    "validation_enabled",
]

# Disable validation in production ETL via env var (R4.4). Default: enabled.
_DISABLED = os.environ.get("ALPHAVAR_VALIDATE", "1").lower() in ("0", "false", "no")


def validation_enabled() -> bool:
    """Whether boundary validation runs (toggle via ALPHAVAR_VALIDATE=0)."""
    return not _DISABLED


def validate(model, df: pd.DataFrame) -> pd.DataFrame:
    """Validate ``df`` against a pandera ``model`` at a layer boundary.

    No-op when disabled (production ETL). Uses ``lazy=True`` to collect all errors.
    """
    if _DISABLED:
        return df
    return model.validate(df, lazy=True)
