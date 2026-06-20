"""Extract the reference layer from an existing wide history frame (R4.6, T25 inc.5) — pure.

``split_reference`` factors the per-instrument constants out of a wide quote frame; this seeds
an SCD-2 history from the contract-level reference, opening every contract version at ``when``
(the data's earliest observation). The asset-level ``AssetMeta`` comes straight from the split.

# 4VERIFY (owner, D2): the migration seeds the SCD history with a single open version per
# contract at ``when`` (the earliest observed timestamp) — historical change before that point
# is not reconstructed (there is no earlier data to reconstruct it from).
"""
import pandas as pd

from alphavar.options.entities import AssetMeta
from alphavar.options.lib.reference._scd import append_on_change
from alphavar.options.lib.reference._split import (
    CONTRACT_KEY_COLUMNS,
    CONTRACT_REF_COLUMNS,
    split_reference,
)


def extract_reference(df: pd.DataFrame, when: pd.Timestamp) -> tuple[AssetMeta, pd.DataFrame]:
    """Factor a wide single-asset frame into ``(AssetMeta, contract SCD-2 history)``.

    The contract history opens one version per contract key at ``when``. When the frame has no
    contract-level reference (e.g. a futures-only asset), the history is empty.
    """
    split = split_reference(df)
    if split.contracts.empty:
        return split.asset, pd.DataFrame()
    key_cols = [c for c in CONTRACT_KEY_COLUMNS if c in split.contracts.columns]
    attr_cols = [c for c in CONTRACT_REF_COLUMNS if c in split.contracts.columns]
    history = append_on_change(pd.DataFrame(), split.contracts, when, key_cols, attr_cols)
    return split.asset, history
