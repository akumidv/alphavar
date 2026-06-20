"""Validation for data-derived path segments (path-traversal protection).

`asset_code`, `asset_name`, `exchange_code` and similar values come from external
sources (exchange APIs, user input) and are interpolated into filesystem paths by the
provider and ETL layers. A crafted value such as ``..`` or one containing a path
separator could escape the data root. Validate every such segment before use.
"""

import re

# Allowlist: letters, digits, dot, underscore, hyphen. Covers real codes like
# ``BTC``, ``ETH_USDC``, ``BTCDVOL_USDC``, ``DERIBIT``.
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9._-]+$")


def validate_path_segment(value: str, *, field: str = "path segment") -> str:
    """Return ``value`` unchanged if it is a safe single path segment, else raise.

    Rejects empty values, anything outside the allowlist, the parent reference ``..``,
    and explicit path separators — i.e. nothing that can traverse out of its directory.
    """
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string, got {value!r}")
    if value in (".", "..") or "/" in value or "\\" in value or not _SAFE_SEGMENT.match(value):
        raise ValueError(
            f"{field} {value!r} is not a valid path segment "
            f'(allowed: letters, digits, ".", "_", "-"; no path separators or "..")'
        )
    return value
