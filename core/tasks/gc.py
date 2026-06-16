from django.conf import settings
from django.db import transaction
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
    logger.info("Starting minio garbage collection")
    base_qs = models.FileAsset.objects.filter(
        status=models.UploadStatus.PENDING,
        created__lt=timezone.now() - timezone.timedelta(seconds=settings.FILE_ORPHANED_INTERVAL),
    )
    with transaction.atomic():
        orphaned_public_file_ids = base_qs.filter(is_public=True).values_list("id", flat=True)
        _ = minio.delete(orphaned_public_file_ids, is_public=True)
        models.FileAsset.objects.filter(id__in=orphaned_public_file_ids).delete()
        orphaned_private_file_ids = base_qs.filter(is_public=False).values_list("id", flat=True)
        _ = minio.delete(orphaned_private_file_ids, is_public=False)
        models.FileAsset.objects.filter(id__in=orphaned_private_file_ids).delete()
    logger.info("Minio garbage collection completed")
    return


@djhuey.db_periodic_task(crontab(minute="30", hour="3"))
@djhuey.lock_task("flush-expired-tokens")
def flush_expired_tokens():
    logger.info("Starting expired JWT token cleanup")
    deleted_count, _ = OutstandingToken.objects.filter(
        expires_at__lt=timezone.now(),
    ).delete()
    logger.info("Expired JWT token cleanup completed", extra={"deleted_count": deleted_count})
    return deleted_count
