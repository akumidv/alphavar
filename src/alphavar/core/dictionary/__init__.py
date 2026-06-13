"""Core (domain-neutral) dictionary: the single entity-name registry (R4.3) and the
neutral classification-axis enums (R4.5)."""
from alphavar.core.dictionary._columns import Col
from alphavar.core.dictionary._registry import column_names, assert_unique
from alphavar.core.dictionary._classification import InstrumentKind, AssetClass, ContractKind

__all__ = [
    "Col", "column_names", "assert_unique",
    "InstrumentKind", "AssetClass", "ContractKind",
]
