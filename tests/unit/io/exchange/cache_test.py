"""T12 equivalence (D2): the cachetools-backed Cache is transparent — a hit returns the
same result as a recompute, and callers get an isolated deep copy (so the cached frame is
never mutated). The eviction policy changed (memory budget -> item count) but does not
affect correctness, which these tests pin.
"""

import pandas as pd

from alphavar.io.exchange.cache import Cache


def test_memoizes_by_arguments():
    cache = Cache(maxsize=16)
    calls = []

    @cache.it
    def load(x):
        calls.append(x)
        return pd.DataFrame({"v": [x]})

    a, b = load(1), load(1)  # same arg -> one underlying call
    c = load(2)  # different arg -> separate call
    assert calls == [1, 2]
    assert a["v"].tolist() == [1] and c["v"].tolist() == [2]
    # a hit returns the same data as the first (transparent)
    assert a.equals(b)


def test_returns_isolated_deep_copy():
    cache = Cache(maxsize=16)

    @cache.it
    def load():
        return pd.DataFrame({"v": [1, 2, 3]})

    first = load()
    first.loc[0, "v"] = 999  # mutate the returned frame
    second = load()  # served from cache
    assert second["v"].tolist() == [1, 2, 3]  # cache untouched
    assert first is not second


def test_none_result_not_cached():
    cache = Cache(maxsize=16)
    calls = []

    @cache.it
    def load():
        calls.append(1)
        return None

    assert load() is None
    assert load() is None
    assert calls == [1, 1]  # None is recomputed, never cached
