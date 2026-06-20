"""Post-fit output checks — sanity of our model results (T21 / R5).

Validate what the model produced: positive IV, an arbitrage-free smile (butterfly via Gatheral
g(k); calendar via monotone ATM total variance across expiries), and a bounded fit residual vs
the market marks. Pure functions over the result DataFrame; nothing mutated.

# 4VERIFY (owner, D2): the butterfly/calendar no-arb criteria and the residual tolerance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.pricer._smile_enrich import _slice_keys, fit_smile_slices
from alphavar.options.lib.validation._report import Severity, ValidationIssue, make_issue


def check_values_positive(df: pd.DataFrame, cols=(OptionsTerm.IV,)) -> list[ValidationIssue]:
    """Model IV (and any given column) should be present and strictly positive after fitting."""
    issues: list[ValidationIssue] = []
    for col in cols:
        if col not in df.columns:
            continue
        bad = (df[col].isna() | (df[col] <= 0)).to_numpy()
        if bad.any():
            issues.append(make_issue("model_values", Severity.WARNING, f"{col} null/non-positive", bad, df.index))
    return issues


def check_fit_residual(
    df: pd.DataFrame,
    market_iv_col: str = OptionsTerm.EXCH_MARK_IV,
    model_iv_col: str = OptionsTerm.IV,
    tol: float = 0.05,
) -> list[ValidationIssue]:
    """Flag rows where the fitted IV departs from the market IV by more than ``tol`` (abs vol)."""
    if market_iv_col not in df.columns or model_iv_col not in df.columns:
        return []
    resid = (df[model_iv_col] - df[market_iv_col]).abs().to_numpy()
    bad = np.isfinite(resid) & (resid > tol)
    if bad.any():
        return [make_issue("fit_residual", Severity.WARNING, f"|model-market| IV > {tol}", bad, df.index)]
    return []


def check_smile_arbitrage(df: pd.DataFrame, model="svi", market_iv_col: str = OptionsTerm.EXCH_MARK_IV):
    """Butterfly (per slice) + calendar (across expiries) static no-arbitrage on the fitted smiles."""
    if market_iv_col not in df.columns:
        return []
    if not {OptionsTerm.STRIKE, OptionsTerm.UNDERLYING_PRICE} <= set(df.columns):
        return []
    fits = fit_smile_slices(df, model=model, market_iv_col=market_iv_col)
    issues: list[ValidationIssue] = []

    # butterfly: each slice's total-variance curve must give a valid density (g(k) ≥ 0)
    butterfly_bad = [key for key, res in fits.items() if not res.is_butterfly_free()]
    if butterfly_bad:
        issues.append(
            ValidationIssue("butterfly_arb", Severity.WARNING, "smile slice(s) not butterfly-free", len(butterfly_bad))
        )

    # calendar: ATM total variance must not decrease as expiry grows (same asset, timestamp)
    calendar_bad = 0
    exp_pos = _slice_keys(df).index(OptionsTerm.EXPIRATION_DATE)
    by_at: dict[tuple, list] = {}
    for key, res in fits.items():
        cal_key = tuple(v for i, v in enumerate(key) if i != exp_pos)  # slice key minus expiration
        by_at.setdefault(cal_key, []).append(res)
    for series in by_at.values():
        series.sort(key=lambda r: r.t_years)
        w_atm = [float(r.total_variance(0.0)) for r in series]
        if any(b < a - 1e-9 for a, b in zip(w_atm, w_atm[1:], strict=False)):
            calendar_bad += 1
    if calendar_bad:
        issues.append(
            ValidationIssue("calendar_arb", Severity.WARNING, "ATM total variance decreases with expiry", calendar_bad)
        )
    return issues
