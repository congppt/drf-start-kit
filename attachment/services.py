from collections.abc import Sequence

from django.db import transaction

from integrations.minio import minio
from utils.log import logger

from .models import FileAsset


def delete_assets(assets: Sequence[FileAsset]) -> int:
    """Delete file rows now, and their MinIO objects after the transaction commits."""
    public_ids = [asset.id for asset in assets if asset.is_public]
    private_ids = [asset.id for asset in assets if not asset.is_public]
    ids = [asset.id for asset in assets]
    if not ids:
        return 0

    deleted, _ = FileAsset.objects.filter(id__in=ids).delete()

    def _delete_minio_objects() -> None:
        errors = minio.delete(public_ids, is_public=True)
        if errors:
            logger.error("Failed to delete public MinIO objects", extra={"errors": [str(e) for e in errors]})
        errors = minio.delete(private_ids, is_public=False)
        if errors:
            logger.error("Failed to delete private MinIO objects", extra={"errors": [str(e) for e in errors]})

    transaction.on_commit(_delete_minio_objects)
    return deleted


def delete_asset(asset: FileAsset) -> None:
    delete_assets([asset])
