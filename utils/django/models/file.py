import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

"""
This module contains the base models for the file system.
To use this module, you need to:
1. Inherit the BaseFileAsset model
2. Inherit the BaseFileAttachment model.
3. Define the relation between the BaseFileAsset and the BaseFileAttachment models, for example:
    class MyFileAsset(BaseFileAsset):
        pass
    class MyFileAttachment(BaseFileAttachment):
        file = models.OneToOneField(MyFileAsset, on_delete=models.CASCADE, related_name='attachment')
"""

class UploadStatus(models.TextChoices):
    PENDING = 'pending'
    READY = 'ready'

class BaseFileAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    is_public = models.BooleanField(default=False)
    owner = models.CharField(max_length=150)
    status = models.CharField(max_length=10, choices=UploadStatus.choices, default=UploadStatus.PENDING, db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class BaseFileAttachment(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64)
    content_object = GenericForeignKey('content_type', 'object_id')
    field_name = models.CharField(max_length=50)

    class Meta:
        abstract = True