"""Data-validation tests (T21): input gate, model checks, clean, report."""

import numpy as np
import pandas as pd
import pytest

from alphavar.options.dictionary import OptionRight, OptionsTerm, Timeframe
from alphavar.options.lib.validation import (
    DataValidationError,
    Severity,
    ValidationReport,
    check_duplicates,
    check_fit_residual,
    check_price_bounds,
    check_required_values,
    check_smile_arbitrage,
    check_strike_sanity,
    check_timestamp_alignment,
    clean,
)


def _frame(forward=100.0, ts="2025-01-01", asset="BTC", t_days=90):
    """A clean, in-bounds option slice (calls), aligned to the EOD grid."""
    strikes = np.linspace(60, 160, 15)
    k = np.log(strikes / forward)
    t = t_days / 365.0
    w = 0.02 + 0.10 * (-0.3 * k + np.sqrt(k**2 + 0.15**2))  # arbitrage-free SVI marks
    iv = np.sqrt(w / t)
    intrinsic = np.maximum(forward - strikes, 0.0)
    timestamp = pd.Timestamp(ts, tz="UTC")
    return pd.DataFrame(
        {
            OptionsTerm.ASSET_CODE: asset,
            OptionsTerm.TIMESTAMP: timestamp,
            OptionsTerm.EXPIRATION_DATE: timestamp + pd.Timedelta(days=t_days),
            OptionsTerm.STRIKE: strikes,
            OptionsTerm.UNDERLYING_PRICE: forward,
            OptionsTerm.OPTION_RIGHT: OptionRight.CALL.value,
            OptionsTerm.PRICE: intrinsic + 1.0,  # time value, all ≤ forward
            OptionsTerm.EXCH_MARK_IV: iv,
        }
    )


# --- report -----------------------------------------------------------------------------------


def test_clean_frame_passes_all_input_checks():
    df = _frame()
    report = ValidationReport()
    for check in (check_required_values, check_price_bounds, check_strike_sanity, check_duplicates):
        report.extend(check(df))
    report.extend(check_timestamp_alignment(df, Timeframe.EOD))
    assert report.ok
    assert len(report) == 0


def test_report_raise_if_errors():
    df = _frame()
    df.loc[0, OptionsTerm.PRICE] = 0.0  # null/zero price → error
    report = ValidationReport().extend(check_required_values(df))
    assert not report.ok
    assert report.errors[0].severity is Severity.ERROR
    with pytest.raises(DataValidationError):
        report.raise_if_errors()


# --- input checks ----------------------------------------------------------------------------


@pytest.mark.parametrize("bad_value", [0.0, np.nan, -1.0])
def test_completeness_flags_null_zero_price(bad_value):
    df = _frame()
    df.loc[2, OptionsTerm.PRICE] = bad_value
    issues = check_required_values(df, required_cols=(OptionsTerm.PRICE,))
    assert issues and issues[0].severity is Severity.ERROR and issues[0].count == 1


def test_completeness_missing_required_column():
    df = _frame().drop(columns=[OptionsTerm.PRICE])
    issues = check_required_values(df, required_cols=(OptionsTerm.PRICE,))
    assert issues[0].severity is Severity.ERROR


def test_price_above_forward_is_scale_error():
    df = _frame()
    df.loc[0, OptionsTerm.PRICE] = df.loc[0, OptionsTerm.UNDERLYING_PRICE] * 5  # call >> forward
    issues = check_price_bounds(df)
    assert any(i.severity is Severity.ERROR and i.check == "price_bounds" for i in issues)


def test_price_below_intrinsic_is_warning():
    df = _frame()
    df.loc[0, OptionsTerm.PRICE] = 0.5  # strike 60, forward 100 → intrinsic 40, far below
    issues = check_price_bounds(df)
    assert any(i.severity is Severity.WARNING and i.check == "price_bounds" for i in issues)


def test_strike_sanity_flags_absurd_strike():
    df = _frame()
    df.loc[0, OptionsTerm.STRIKE] = 1_000_000.0  # forward 100, band 100 → far out
    issues = check_strike_sanity(df)
    assert issues and issues[0].severity is Severity.ERROR


def test_timestamp_misaligned_is_error():
    df = _frame()
    df.loc[0, OptionsTerm.TIMESTAMP] = pd.Timestamp("2025-01-01 12:00", tz="UTC")  # not on EOD grid
    issues = check_timestamp_alignment(df, Timeframe.EOD)
    assert any(i.check == "timestamp" and i.severity is Severity.ERROR for i in issues)


def test_timestamp_tz_naive_is_error():
    df = _frame()
    df[OptionsTerm.TIMESTAMP] = df[OptionsTerm.TIMESTAMP].dt.tz_localize(None)
    issues = check_timestamp_alignment(df, Timeframe.EOD)
    assert issues[0].severity is Severity.ERROR


def test_duplicates_flagged():
    df = pd.concat([_frame(), _frame().iloc[[0]]], ignore_index=True)  # row 0 duplicated
    issues = check_duplicates(df)
    assert issues and issues[0].severity is Severity.ERROR and issues[0].count == 2


# --- model checks ----------------------------------------------------------------------------


def test_smile_arbitrage_free_slice_has_no_issues():
    df = _frame()
    df[OptionsTerm.IV] = df[OptionsTerm.EXCH_MARK_IV]
    assert check_smile_arbitrage(df, model="svi") == []


def test_calendar_arbitrage_detected():
    # near expiry has *higher* ATM total variance than far expiry → calendar arb
    near = _frame(t_days=30)
    near[OptionsTerm.EXCH_MARK_IV] = near[OptionsTerm.EXCH_MARK_IV] * 3.0
    far = _frame(t_days=300)
    df = pd.concat([near, far], ignore_index=True)
    issues = check_smile_arbitrage(df, model="svi")
    assert any(i.check == "calendar_arb" for i in issues)


def test_fit_residual_flags_large_gap():
    df = _frame()
    df[OptionsTerm.IV] = df[OptionsTerm.EXCH_MARK_IV] + 0.2  # 0.2 vol off everywhere
    issues = check_fit_residual(df, tol=0.05)
    assert issues and issues[0].severity is Severity.WARNING


# --- clean (opt-in remediation) --------------------------------------------------------------


def test_clean_defaults_are_noop():
    df = _frame()
    pd.testing.assert_frame_equal(clean(df), df.reset_index(drop=True))


def test_clean_drops_null_price():
    df = _frame()
    df.loc[0, OptionsTerm.PRICE] = np.nan
    out = clean(df, drop_na_price=True)
    assert len(out) == len(df) - 1
    assert out[OptionsTerm.PRICE].notna().all()


def test_clean_drops_duplicates():
    df = pd.concat([_frame(), _frame().iloc[[0]]], ignore_index=True)
    out = clean(df, drop_duplicates=True)
    assert len(out) == len(_frame())


def test_clean_rounds_timestamp():
    df = _frame()
    df.loc[0, OptionsTerm.TIMESTAMP] = pd.Timestamp("2025-01-01 12:00", tz="UTC")
    out = clean(df, round_timestamp=Timeframe.EOD)
    assert (out[OptionsTerm.TIMESTAMP] == pd.Timestamp("2025-01-01", tz="UTC")).all()


# --- facade ----------------------------------------------------------------------------------


def test_facade_validate_input_and_clean(option_data):
    from alphavar.options.validation_class import OptionsValidation

    df = _frame()
    df.loc[0, OptionsTerm.PRICE] = 0.0  # an error to detect
    option_data.df_hist = pd.concat([df, df.iloc[[1]]], ignore_index=True)  # + a duplicate
    val = OptionsValidation(option_data)

    report = val.validate_input()
    assert not report.ok
    assert {i.check for i in report.errors} >= {"completeness", "duplicates"}

    val.clean(drop_duplicates=True, drop_na_price=True)
    assert val.validate_input().ok


def test_facade_validate_model(option_data):
    from alphavar.options.validation_class import OptionsValidation

    df = _frame()
    df[OptionsTerm.IV] = df[OptionsTerm.EXCH_MARK_IV]
    option_data.df_hist = df
    assert OptionsValidation(option_data).validate_model().ok
