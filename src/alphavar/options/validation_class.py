"""Data-validation facade component (R3, T21).

Aggregated by ``Option`` over the shared ``OptionsData`` (like enrichment/chain/pricer). Pure
checks live in ``options.lib.validation``; this class orchestrates them over ``df_hist`` at the
two stages and exposes the opt-in ``clean``.

  - ``validate_input()`` — pre-analysis data quality (completeness, no-arb price bounds, strike
    sanity, timestamp/timeframe alignment, duplicates).
  - ``validate_model()`` — post-fit sanity (positive IV, butterfly + calendar no-arb, fit residual).
  - ``clean(...)`` — opt-in remediation (drop dup / drop null price / round timestamp).
"""
from __future__ import annotations

from typing import Self

from alphavar.options.dictionary import OptionsTerm
from alphavar.options.lib.validation import (
    ValidationReport,
    check_duplicates,
    check_fit_residual,
    check_price_bounds,
    check_required_values,
    check_smile_arbitrage,
    check_strike_sanity,
    check_timestamp_alignment,
    check_values_positive,
    clean,
)
from alphavar.options.option_data_class import OptionsData


class OptionsValidation:
    """Semantic data validation over OptionsData (pre-analysis + post-fit)."""

    def __init__(self, data: OptionsData):
        self.data = data

    def validate_input(
        self,
        required_cols=(OptionsTerm.PRICE,),
        raise_on_error: bool = False,
    ) -> ValidationReport:
        """Pre-analysis data-quality gate over ``df_hist``. Returns a report (raises only when
        ``raise_on_error`` and an error-severity issue is found)."""
        df = self.data.df_hist
        report = ValidationReport()
        report.extend(check_required_values(df, required_cols))
        report.extend(check_price_bounds(df))
        report.extend(check_strike_sanity(df))
        report.extend(check_timestamp_alignment(df, self.data.timeframe))
        report.extend(check_duplicates(df))
        if raise_on_error:
            report.raise_if_errors()
        return report

    def validate_model(
        self,
        market_iv_col: str = OptionsTerm.EXCH_MARK_IV,
        model_iv_col: str = OptionsTerm.IV,
        smile_model: str = "svi",
        raise_on_error: bool = False,
    ) -> ValidationReport:
        """Post-fit model sanity over ``df_hist`` (positive IV, smile no-arb, fit residual)."""
        df = self.data.df_hist
        report = ValidationReport()
        report.extend(check_values_positive(df, cols=(model_iv_col,)))
        report.extend(check_smile_arbitrage(df, model=smile_model, market_iv_col=market_iv_col))
        report.extend(check_fit_residual(df, market_iv_col=market_iv_col, model_iv_col=model_iv_col))
        if raise_on_error:
            report.raise_if_errors()
        return report

    def clean(self, drop_duplicates: bool = False, drop_na_price: bool = False, round_timestamp=None) -> Self:
        """Opt-in remediation of ``df_hist`` (all fixes default off); mutates the shared data."""
        self.data.df_hist = clean(
            self.data.df_hist,
            drop_duplicates=drop_duplicates,
            drop_na_price=drop_na_price,
            round_timestamp=round_timestamp,
        )
        return self
