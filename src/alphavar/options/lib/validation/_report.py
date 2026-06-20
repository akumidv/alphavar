"""Validation report model: severity-tagged issues, non-mutating (T21 / R3).

The ``validation`` component *detects* and reports; it never silently rewrites data. A check
is a pure function returning ``ValidationIssue``s; the facade aggregates them into a
``ValidationReport``. Remediation is a separate, opt-in ``clean`` step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

_MAX_ROWS = 20  # cap offending-row labels kept per issue (diagnostics, not the full set)


class Severity(StrEnum):
    """Issue severity. ``ERROR`` = must fix before analysis; ``WARNING`` = review."""

    ERROR = "error"
    WARNING = "warning"


class DataValidationError(ValueError):
    """Raised by ``ValidationReport.raise_if_errors`` when error-severity issues exist."""


@dataclass(frozen=True)
class ValidationIssue:
    """One failed check: what, how bad, how many rows, a sample of offending labels."""

    check: str
    severity: Severity
    message: str
    count: int = 0
    rows: tuple = field(default_factory=tuple)


@dataclass
class ValidationReport:
    """Aggregated issues from one validation pass."""

    issues: list[ValidationIssue] = field(default_factory=list)

    def extend(self, issues: list[ValidationIssue]) -> ValidationReport:
        self.issues.extend(issues)
        return self

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity is Severity.WARNING]

    @property
    def ok(self) -> bool:
        """True when there are no error-severity issues (warnings allowed)."""
        return not self.errors

    def raise_if_errors(self) -> ValidationReport:
        """Raise ``DataValidationError`` if any error-severity issue is present."""
        if self.errors:
            raise DataValidationError(f"{len(self.errors)} validation error(s): {self.summary()}")
        return self

    def summary(self) -> str:
        if not self.issues:
            return "ok (no issues)"
        return "; ".join(f"[{i.severity}] {i.check}: {i.message}" for i in self.issues)

    def __bool__(self) -> bool:
        return self.ok

    def __len__(self) -> int:
        return len(self.issues)


def make_issue(check: str, severity: Severity, message: str, mask, index) -> ValidationIssue:
    """Build an issue from a boolean ``mask`` over ``index`` (count + a capped row sample)."""
    labels = list(index[mask])
    return ValidationIssue(check, severity, message, count=len(labels), rows=tuple(labels[:_MAX_ROWS]))
