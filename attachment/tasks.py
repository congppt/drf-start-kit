from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from huey import crontab
from huey.contrib import djhuey

from utils.log import logger

from .models import FileAsset, UploadStatus
from .services import delete_assets


@djhuey.db_periodic_task(crontab(minute="0", hour="0"))
@djhuey.lock_task("minio-garbage-collect")
def minio_garbage_collect():
    """
    Remove abandoned uploads that were never saved on a record.

    Ready files are deleted by the update that replaces or clears them.
    """
    logger.info("Starting minio garbage collection")
    cutoff = timezone.now() - timedelta(seconds=settings.FILE_ORPHANED_INTERVAL)
    assets = list(
        FileAsset.objects.filter(
            status=UploadStatus.PENDING,
            created_at__lt=cutoff,
        ).only("id", "is_public")
    )

    with transaction.atomic():
        deleted = delete_assets(assets)

    logger.info("Minio garbage collection completed", extra={"deleted_count": deleted})
    return deleted
