"""Thread-safe TTL cache for exchange API DataFrame results (T12).

Backed by ``cachetools.TTLCache`` + a plain ``threading.Lock`` (replaces a hand-rolled
cache with concurrency flaws — timeout-ignoring locks, cross-thread release, a DataFrame
used as a concurrent index, ``sys.getsizeof`` memory estimates). Eviction is now by item
count + TTL (was an ad-hoc memory budget via ``psutil``).

The ``.it`` decorator memoizes a function's result keyed by its arguments and returns a
**deep copy** on every call, so callers can never mutate the cached frame.

# 4VERIFY (owner, D2): eviction semantics change (memory budget -> maxsize
# item count); the first ``Cache(128, …)`` positional now means 128 cached items, not MB.
"""

import hashlib
import threading
from copy import deepcopy
from functools import wraps

import pandas as pd
from cachetools import TTLCache


class Cache:  # pylint: disable=too-few-public-methods
    """TTL cache exposing a thread-safe ``.it`` memoizing decorator."""

    DEFAULT_TTL_SECONDS = 30 * 60  # 30 minutes (was EXPIRATION_DELTA_MINUTES)

    def __init__(
        self, maxsize: int = 128, ttl_seconds: float = DEFAULT_TTL_SECONDS, is_new_day_ttl_reset: bool = False
    ):
        # is_new_day_ttl_reset: accepted for backward compatibility; a midnight reset was
        # never implemented in the previous version either.
        self._is_new_day_ttl_reset = is_new_day_ttl_reset
        self._lock = threading.Lock()
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)

    def it(self, func):
        """Memoize ``func`` by its arguments; hand back a deep copy on every call."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = self._get_key(func.__name__, *self._norm_args(args, func.__name__), **kwargs)
            with self._lock:
                hit = self._cache.get(key)
            if hit is not None:
                return self._copy(hit)
            result = func(*args, **kwargs)
            if result is not None:
                with self._lock:
                    self._cache[key] = result
            return self._copy(result)

        return wrapper

    @staticmethod
    def _norm_args(args: tuple, func_name: str) -> tuple:
        # args[0] is ``self`` when ``.it`` wraps a bound method — drop it from the key.
        if args and hasattr(args[0], func_name):
            return args[1:]
        return args

    @staticmethod
    def _copy(value):
        if isinstance(value, pd.DataFrame):
            return value.copy(deep=True)
        return deepcopy(value)

    @staticmethod
    def _get_key(data_type, *args, **kwargs) -> int:
        key_args = list(args) + (list(kwargs.values()) if kwargs else [])
        key_str = data_type + "_" + (",".join(str(val) for val in key_args) if key_args else "")
        return int(hashlib.sha256(key_str.encode("utf-8")).hexdigest(), 16) % (10**16)
