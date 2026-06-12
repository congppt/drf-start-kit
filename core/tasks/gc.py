from django.conf import settings
from django.db import transaction
from django.utils import timezone
from huey.contrib import djhuey
from huey import crontab

from .. import models
from utils.minio import minio

@djhuey.db_periodic_task(crontab(minute="0", hour="0"))
@djhuey.lock_task("minio-garbage-collect")
def minio_garbage_collect():
    base_qs = models.FileAsset.objects.filter(
        status=models.UploadStatus.PENDING,
        created__lt=timezone.now() - timezone.timedelta(seconds=settings.FILE_ORPHANED_INTERVAL)
    )
    with transaction.atomic():
        orphaned_public_file_ids = base_qs.filter(is_public=True).values_list('id', flat=True)
        _ = minio.delete(orphaned_public_file_ids, is_public=True)
        models.FileAsset.objects.filter(id__in=orphaned_public_file_ids).delete()
        orphaned_private_file_ids = base_qs.filter(is_public=False).values_list('id', flat=True)
        _ = minio.delete(orphaned_private_file_ids, is_public=False)
        models.FileAsset.objects.filter(id__in=orphaned_private_file_ids).delete()
    return
