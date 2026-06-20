"""Helpers over column-name registries (R4.3).

A registry is a plain class whose UPPER_CASE attributes are ``str`` column names
(see ``Term``). These helpers introspect it without depending on enum machinery.
"""

from collections.abc import Iterable


def column_names(*registries: type) -> list[str]:
    """All string column names declared on the given registry class(es).

    Reads UPPER_CASE str attributes; includes inherited ones (domain extends core).
    """
    names: list[str] = []
    seen: set[str] = set()
    for registry in registries:
        for attr in dir(registry):
            if not attr.isupper():
                continue
            value = getattr(registry, attr)
            if isinstance(value, str) and value not in seen:
                seen.add(value)
                names.append(value)
    return names


def assert_unique(*registries: type) -> None:
    """Raise if any column-name value is declared twice across the registries.

    Enforces the ``@enum.unique`` guarantee the old enum gave us (R4.3).
    """
    values: list[str] = []
    for registry in registries:
        for attr in dir(registry):
            if attr.isupper() and isinstance(getattr(registry, attr), str):
                values.append(getattr(registry, attr))
    duplicates = _duplicates(values)
    if duplicates:
        raise ValueError(f"Duplicate column names in registry: {sorted(duplicates)}")


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    dups: set[str] = set()
    for value in values:
        if value in seen:
            dups.add(value)
        seen.add(value)
    return dups
