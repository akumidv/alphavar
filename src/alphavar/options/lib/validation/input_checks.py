"""Pre-analysis input checks — data quality before fitting/analysis (T21).

Semantic value checks distinct from the pandera schemas (structure/dtype/nullability) and
``validate_book_data`` (the exchange→storage boundary, T23.5). Each is a pure function over a
DataFrame returning ``ValidationIssue``s; nothing is mutated.

# 4VERIFY (owner, D2): the no-arbitrage price bounds (call ≤ F, put ≤ K, ≥ intrinsic), the
# strike sanity band, and the timeframe-alignment rule. Tolerances are configurable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from alphavar.options.dictionary import OptionRight, OptionsTerm, Timeframe
from alphavar.options.lib.validation._report import Severity, ValidationIssue, make_issue

# columns whose value must be present and strictly positive before analysis (R4.2)
_POSITIVE_VALUE_COLS = (OptionsTerm.PRICE, OptionsTerm.IV)


def check_required_values(df: pd.DataFrame, required_cols=(OptionsTerm.PRICE,)) -> list[ValidationIssue]:
    """Required columns must be present and free of NaN/None (and > 0 for price/iv)."""
    issues: list[ValidationIssue] = []
    for col in required_cols:
        if col not in df.columns:
            issues.append(ValidationIssue("completeness", Severity.ERROR, f"required column {col!r} missing", len(df)))
            continue
        bad = df[col].isna()
        if col in _POSITIVE_VALUE_COLS:
            bad = bad | (df[col] <= 0)
        if bad.any():
            issues.append(make_issue("completeness", Severity.ERROR, f"{col} null/zero", bad.to_numpy(), df.index))
    return issues


def check_price_bounds(df: pd.DataFrame, tol: float = 0.01) -> list[ValidationIssue]:
    """No-arbitrage price bounds (undiscounted forward): a breach of the **upper** bound
    (call > F, put > K) signals a scale/parse error → ERROR; below intrinsic → WARNING."""
    need = {OptionsTerm.PRICE, OptionsTerm.UNDERLYING_PRICE, OptionsTerm.STRIKE, OptionsTerm.OPTION_RIGHT}
    if not need <= set(df.columns):
        return []
    forward = df[OptionsTerm.UNDERLYING_PRICE].to_numpy(dtype=float)
    strike = df[OptionsTerm.STRIKE].to_numpy(dtype=float)
    price = df[OptionsTerm.PRICE].to_numpy(dtype=float)
    is_call = (df[OptionsTerm.OPTION_RIGHT] == OptionRight.CALL.value).to_numpy()
    finite = np.isfinite(forward) & np.isfinite(strike) & np.isfinite(price)

    upper = np.where(is_call, forward, strike)
    intrinsic = np.where(is_call, np.maximum(forward - strike, 0.0), np.maximum(strike - forward, 0.0))
    over = finite & (price > upper * (1.0 + tol))
    under = finite & (price < intrinsic * (1.0 - tol))

    issues: list[ValidationIssue] = []
    if over.any():
        msg = "price above no-arb cap (scale/parse?)"
        issues.append(make_issue("price_bounds", Severity.ERROR, msg, over, df.index))
    if under.any():
        issues.append(make_issue("price_bounds", Severity.WARNING, "price below intrinsic", under, df.index))
    return issues


def check_strike_sanity(df: pd.DataFrame, band: float = 100.0) -> list[ValidationIssue]:
    """Strike must be positive and within ``[F/band, F·band]`` of the forward (else a parse error)."""
    if not {OptionsTerm.STRIKE, OptionsTerm.UNDERLYING_PRICE} <= set(df.columns):
        return []
    forward = df[OptionsTerm.UNDERLYING_PRICE].to_numpy(dtype=float)
    strike = df[OptionsTerm.STRIKE].to_numpy(dtype=float)
    finite = np.isfinite(forward) & np.isfinite(strike) & (forward > 0)
    bad = finite & ((strike <= 0) | (strike < forward / band) | (strike > forward * band))
    if bad.any():
        return [make_issue("strike_sanity", Severity.ERROR, "strike implausibly far from forward", bad, df.index)]
    return []


def check_timestamp_alignment(df: pd.DataFrame, timeframe: Timeframe) -> list[ValidationIssue]:
    """``timestamp`` must be tz-aware and aligned to the timeframe grid; sub-ms resolution → WARNING."""
    col = OptionsTerm.TIMESTAMP
    if col not in df.columns:
        return []
    ts = df[col]
    if ts.dt.tz is None:
        return [ValidationIssue("timestamp", Severity.ERROR, "timestamp is tz-naive", len(df))]
    issues: list[ValidationIssue] = []
    misaligned = (ts != ts.dt.floor(timeframe.offset)).to_numpy()
    if misaligned.any():
        issues.append(
            make_issue("timestamp", Severity.ERROR, f"not aligned to {timeframe.value} grid", misaligned, df.index)
        )
    # sub-millisecond component (resolution-independent: works for s/ms/us/ns dtypes)
    sub_ms = ((ts.dt.microsecond % 1000 != 0) | (ts.dt.nanosecond != 0)).to_numpy()
    if sub_ms.any():
        issues.append(make_issue("timestamp", Severity.WARNING, "sub-millisecond resolution", sub_ms, df.index))
    return issues


def natural_key(df: pd.DataFrame) -> list[str]:
    """The row-identity key for duplicate detection (contract + timestamp), columns present only."""
    if OptionsTerm.EXCH_SYMBOL in df.columns:
        candidate = [OptionsTerm.EXCH_SYMBOL, OptionsTerm.TIMESTAMP]
    else:
        candidate = [
            OptionsTerm.ASSET_CODE,
            OptionsTerm.EXPIRATION_DATE,
            OptionsTerm.STRIKE,
            OptionsTerm.OPTION_RIGHT,
            OptionsTerm.TIMESTAMP,
        ]
    return [c for c in candidate if c in df.columns]


def check_duplicates(df: pd.DataFrame) -> list[ValidationIssue]:
    """No duplicate rows on the natural ``(contract, timestamp)`` key."""
    keys = natural_key(df)
    if not keys:
        return []
    dup = df.duplicated(subset=keys, keep=False).to_numpy()
    if dup.any():
        return [make_issue("duplicates", Severity.ERROR, f"duplicate rows on {keys}", dup, df.index)]
    return []
