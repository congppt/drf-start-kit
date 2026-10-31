"""
Readiness checks for services this project always runs, plus checks from installed apps.

An optional app adds a check by defining ``AppConfig.readiness_checks``:

    def readiness_checks(self):
        return {"minio": check_minio}

Removing the app from ``INSTALLED_APPS`` removes its checks. A check takes no arguments
and returns ``True`` when healthy, ``False`` when unhealthy, or ``None`` when that
service is not configured. ``None`` does not fail the probe.
"""

import time
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.http import JsonResponse

PROBE_TIMEOUT_SECONDS = 1

ReadinessCheck = Callable[[], bool | None]
_CORE_CHECK_NAMES = frozenset({"database", "redis"})


def _check_database() -> bool:
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    finally:
        connection.close()


def _check_redis() -> bool | None:
    backend = settings.CACHES["default"]["BACKEND"]
    if "dummy" in backend.lower():
        return None

    import redis

    client = redis.Redis.from_url(
        settings.CACHES["default"]["LOCATION"],
        socket_connect_timeout=PROBE_TIMEOUT_SECONDS,
        socket_timeout=PROBE_TIMEOUT_SECONDS,
    )
    try:
        return bool(client.ping())
    finally:
        client.close()


def core_readiness_checks() -> dict[str, ReadinessCheck]:
    return {
        "database": _check_database,
        "redis": _check_redis,
    }


def app_readiness_checks() -> dict[str, ReadinessCheck]:
    """Collect checks from installed apps that define ``readiness_checks``."""
    checks: dict[str, ReadinessCheck] = {}
    for config in apps.get_app_configs():
        provider = getattr(config, "readiness_checks", None)
        if not callable(provider):
            continue
        provided = provider()
        if not isinstance(provided, Mapping):
            raise ImproperlyConfigured(f"{config.name}.readiness_checks() must return a mapping of name to callable")
        for name, checker in provided.items():
            if name in _CORE_CHECK_NAMES or name in checks:
                raise ImproperlyConfigured(f"{config.name} readiness check {name!r} duplicates an existing check")
            if not callable(checker):
                raise ImproperlyConfigured(f"{config.name} readiness check {name!r} must be callable")
            checks[name] = checker
    return checks


def run_checks(checkers: Mapping[str, ReadinessCheck]) -> dict[str, bool | None]:
    pool = ThreadPoolExecutor(max_workers=len(checkers))
    futures = {name: pool.submit(checker) for name, checker in checkers.items()}
    deadline = time.monotonic() + PROBE_TIMEOUT_SECONDS
    checks: dict[str, bool | None] = {}
    try:
        for name, future in futures.items():
            remaining = deadline - time.monotonic()
            if future.done():
                try:
                    checks[name] = future.result()
                except Exception:
                    checks[name] = False
            elif remaining <= 0:
                checks[name] = False
            else:
                try:
                    checks[name] = future.result(timeout=remaining)
                except Exception:
                    checks[name] = False
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    return checks


def probe_response(checks: Mapping[str, bool | None]) -> JsonResponse:
    healthy = all(value is not False for value in checks.values())
    return JsonResponse(
        {"success": healthy, "checks": checks},
        status=200 if healthy else 503,
    )
