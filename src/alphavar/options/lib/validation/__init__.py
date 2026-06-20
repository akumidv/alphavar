"""Data validation — semantic value checks + opt-in remediation (T21 / R3).

Distinct from the pandera schemas (structure/dtype/nullability) and ``validate_book_data``
(exchange→storage boundary, T23.5): these are cross-field, no-arbitrage and quality checks on
the actual values, at two stages — a pre-analysis **input** gate and a post-fit **model** check.
Detection is non-mutating (``ValidationReport``); ``clean`` is the opt-in fix step.
"""
from alphavar.options.lib.validation._report import (
    DataValidationError,
    Severity,
    ValidationIssue,
    ValidationReport,
)
from alphavar.options.lib.validation.clean import clean
from alphavar.options.lib.validation.input_checks import (
    check_duplicates,
    check_price_bounds,
    check_required_values,
    check_strike_sanity,
    check_timestamp_alignment,
    natural_key,
)
from alphavar.options.lib.validation.model_checks import (
    check_fit_residual,
    check_smile_arbitrage,
    check_values_positive,
)

__all__ = [
    "Severity",
    "ValidationIssue",
    "ValidationReport",
    "DataValidationError",
    "check_required_values",
    "check_price_bounds",
    "check_strike_sanity",
    "check_timestamp_alignment",
    "check_duplicates",
    "natural_key",
    "check_values_positive",
    "check_fit_residual",
    "check_smile_arbitrage",
    "clean",
]
