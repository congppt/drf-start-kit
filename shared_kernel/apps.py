from django.apps import AppConfig
from django.conf import settings
from django.db import connection

from shared_kernel.health import PROBE_TIMEOUT_SECONDS


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


class SharedKernelConfig(AppConfig):
    name = "shared_kernel"

    def readiness_checks(self):
        return {
            "database": _check_database,
            "redis": _check_redis,
        }
