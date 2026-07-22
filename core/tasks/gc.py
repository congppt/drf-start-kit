from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone
from huey import crontab
from huey.contrib import djhuey
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from integrations.minio import minio
from utils.log import logger

from .. import models


@djhuey.db_periodic_task(crontab(minute="0", hour="0"))
@djhuey.lock_task("minio-garbage-collect")
def minio_garbage_collect():
    """
    Remove FileAsset rows that are no longer referenced, then delete MinIO objects.

    Covers:
    - abandoned PENDING uploads that were never attached
    - READY assets left unattached after detachment/replacement
    """
    logger.info("Starting minio garbage collection")
    cutoff = timezone.now() - timedelta(seconds=settings.FILE_ORPHANED_INTERVAL)
    assets = list(
        models.FileAsset.objects.filter(
            ~Exists(models.FileAttachment.objects.filter(file_id=OuterRef("pk"))),
            created__lt=cutoff,
        ).only("id", "is_public")
    )

    public_ids = [asset.id for asset in assets if asset.is_public]
    private_ids = [asset.id for asset in assets if not asset.is_public]
    ids = [asset.id for asset in assets]

    def _delete_minio_objects(public_ids: list, private_ids: list) -> None:
        errors = minio.delete(public_ids, is_public=True)
        if errors:
            logger.error("Failed to delete public MinIO objects", extra={"errors": [str(e) for e in errors]})
        errors = minio.delete(private_ids, is_public=False)
        if errors:
            logger.error("Failed to delete private MinIO objects", extra={"errors": [str(e) for e in errors]})

    with transaction.atomic():
        deleted, _ = models.FileAsset.objects.filter(id__in=ids).delete()
        transaction.on_commit(lambda: _delete_minio_objects(public_ids, private_ids))

    logger.info("Minio garbage collection completed", extra={"deleted_count": deleted})
    return deleted


@djhuey.db_periodic_task(crontab(minute="30", hour="3"))
@djhuey.lock_task("flush-expired-tokens")
def flush_expired_tokens():
    logger.info("Starting expired JWT token cleanup")
    deleted_count, _ = OutstandingToken.objects.filter(
        expires_at__lt=timezone.now(),
    ).delete()
    logger.info("Expired JWT token cleanup completed", extra={"deleted_count": deleted_count})
    return deleted_count
