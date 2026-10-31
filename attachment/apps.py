from django.apps import AppConfig


def _check_minio() -> bool | None:
    from integrations.minio import minio
    from shared_kernel.health import PROBE_TIMEOUT_SECONDS

    return minio.health_check(timeout=PROBE_TIMEOUT_SECONDS)


class AttachmentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "attachment"

    def readiness_checks(self):
        return {"minio": _check_minio}
