from __future__ import annotations

import hashlib
import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from django.core.cache import cache
from djangorestframework_camel_case.render import CamelCaseJSONRenderer

P = ParamSpec("P")
R = TypeVar("R")

_MISSING = object()
__RENDERER = CamelCaseJSONRenderer()


def _get_version_key(key: str) -> str:
    # Keep a separate namespace for version keys to avoid collisions.
    return f"__ver__:{key}"


def _get_cache_version(base_key: str) -> int:
    version_key = _get_version_key(base_key)
    v = cache.get(version_key)
    if isinstance(v, int) and v >= 1:
        return v
    # Initialize to 1 if missing/invalid.
    cache.set(version_key, 1, timeout=None)
    return 1


def bump_cache_version(key: str) -> int:
    """
    Increment the version for a base key.

    This invalidates all keys generated via `cached(key=base_key, ...)` (including
    arg/kwarg variants) without needing to enumerate and delete them.
    """

    version_key = _get_version_key(key)

    # Some backends support atomic incr; others may raise.
    try:
        cache.add(version_key, 1, timeout=None)
        v = cache.incr(version_key)
        return int(v)
    except Exception:
        current = cache.get(version_key)
        try:
            current_int = int(current) if current is not None else 1
        except Exception:
            current_int = 1
        next_version = max(1, current_int) + 1
        cache.set(version_key, next_version, timeout=None)
        return next_version


def clear_cache(base_key: str) -> None:
    """
    Unified cache invalidation for `cached(key=...)`.
    - Bumps the base key version so all arg/kwarg variants are effectively flushed.
    - Old cached values will be deleted automatically after timeout.
    """
    bump_cache_version(base_key)


def _canonical_arguments_payload(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """
    Map a concrete call's args/kwargs to a stable dict of parameter name -> value
    so that equivalent calls (e.g. f(1) vs f(x=1)) share the same cache key.

    If the call cannot be bound to the function's signature, fall back to the raw
    args/kwargs shape (legacy behavior).
    """

    try:
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
    except (TypeError, ValueError):
        return {"args": args, "kwargs": kwargs}

    return {name: bound.arguments[name] for name in sorted(bound.arguments)}


def _stable_arg_hash(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    canonical = _canonical_arguments_payload(func, args, kwargs)
    payload = __RENDERER.render(canonical)
    return hashlib.sha256(payload).hexdigest()


def make_cache_key(
    *,
    key: str,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    vary_on_args: bool = True,
) -> str:
    version = _get_cache_version(key)
    if not vary_on_args:
        return f"{key}:v{version}"
    return f"{key}:v{version}:{func.__module__}.{func.__qualname__}:{_stable_arg_hash(func, args, kwargs)}"


def delete_cache(
    *,
    base_key: str,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    vary_on_args: bool = True,
) -> None:
    """
    Delete one specific cached entry (when you know the exact call signature).

    Prefer `delete_cache(key)` when you want to flush all variants.
    """
    key = make_cache_key(key=base_key, func=func, args=args, kwargs=kwargs, vary_on_args=vary_on_args)
    cache.delete(key)


def cached(
    base_key: str,
    ttl: int | None,
    *,
    vary_on_args: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Cache a function's return value using Django's default cache backend.

    Args:
        key: Base cache key.
        ttl: Time-to-live in seconds. Pass None to cache forever.
        vary_on_args: If True, include a stable hash of the call in the cache key.
            Positional and keyword forms of the same arguments map to one key
            (via signature binding); otherwise falls back to hashing raw args/kwargs.
    """

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            cache_key = make_cache_key(
                key=base_key,
                func=fn,
                args=args,  # type: ignore[arg-type]
                kwargs=kwargs,  # type: ignore[arg-type]
                vary_on_args=vary_on_args,
            )

            cached_value = cache.get(cache_key, default=_MISSING)
            if cached_value is not _MISSING:
                return cached_value  # type: ignore[return-value]

            result = fn(*args, **kwargs)
            cache.set(cache_key, result, timeout=ttl)
            return result

        return wrapper

    return decorator
