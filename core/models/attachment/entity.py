import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .enums import UploadStatus


class FileAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    is_public = models.BooleanField(default=False)
    owner = models.CharField(max_length=150)
    status = models.CharField(max_length=10, choices=UploadStatus.choices, default=UploadStatus.PENDING, db_index=True)
    created = models.DateTimeField(auto_now_add=True)

class FileAttachment(models.Model):
    file = models.ForeignKey(FileAsset, on_delete=models.CASCADE, related_name='attachments')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64)
    content_object = GenericForeignKey('content_type', 'object_id')
    field_name = models.CharField(max_length=50)