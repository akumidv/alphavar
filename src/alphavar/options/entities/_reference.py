"""Reference (non-time-series) instrument metadata entities (R4.6, T25).

Per-asset constants that quote frames otherwise repeat on every row. ``AssetMeta`` is the
asset-level layer (one record per ``asset_code``); contract-level reference (per
``exch_symbol`` / option key) is carried as a deduplicated frame, not per-row.
"""
from pydantic import BaseModel, ConfigDict


class AssetMeta(BaseModel):
    """Asset-level reference: properties of an ``asset_code`` that don't vary by row or time
    within one stored series (R4.6). Field names match the column registry so it builds
    directly from a row's constant values."""

    model_config = ConfigDict(extra="ignore")

    asset_code: str
    instrument_kind: str | None = None
    asset_class: str | None = None
    currency: str | None = None
    contract_kind: str | None = None
    title: str | None = None
