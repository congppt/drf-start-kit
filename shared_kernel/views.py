import time
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.urls import path

PROBE_TIMEOUT_SECONDS = 1


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


def _check_minio() -> bool | None:
    from integrations.minio import minio

    return minio.health_check(timeout=PROBE_TIMEOUT_SECONDS)


def _run_checks(checkers: dict) -> dict[str, bool | None]:
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


def _probe_response(checks: dict[str, bool | None]) -> JsonResponse:
    healthy = all(value is not False for value in checks.values())
    return JsonResponse(
        {"success": healthy, "checks": checks},
        status=200 if healthy else 503,
    )


def liveness(_request):
    return JsonResponse({"success": True})


def readiness(_request):
    checks = _run_checks(
        {
            "database": _check_database,
            "redis": _check_redis,
            "minio": _check_minio,
        }
    )
    return _probe_response(checks)


urlpatterns = [
    path("health/live/", liveness, name="health_liveness"),
    path("health/ready/", readiness, name="health_readiness"),
]
