from django.conf import settings
from django.core.cache import caches
from django.db import connection
from django.http import JsonResponse
from django.urls import path


def _check_database() -> bool:
    connection.ensure_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return True


def _check_redis() -> bool | None:
    backend = settings.CACHES["default"]["BACKEND"]
    if "dummy" in backend.lower():
        return None
    cache = caches["default"]
    cache.set("__health__", "1", timeout=5)
    return cache.get("__health__") == "1"


def _check_minio() -> bool | None:
    import env

    if not env.MINIO_ENDPOINT:
        return None
    from integrations.minio import minio

    minio.client.bucket_exists(env.MINIO_PRIVATE_BUCKET)
    return True


def health_check(_request):
    checks: dict[str, bool | None] = {}
    healthy = True

    for name, checker in (
        ("database", _check_database),
        ("redis", _check_redis),
        ("minio", _check_minio),
    ):
        try:
            checks[name] = checker()
        except Exception:
            checks[name] = False

        if checks[name] is False:
            healthy = False

    return JsonResponse(
        {"success": healthy, "checks": checks},
        status=200 if healthy else 503,
    )


urlpatterns = [
    path("health/", health_check, name="health_check"),
]
