from django.db import models

from utils.django.models.file import BaseFileAsset, BaseFileAttachment, UploadStatus

class FileAsset(BaseFileAsset):
    pass

class FileAttachment(BaseFileAttachment):
    file = models.OneToOneField(FileAsset, on_delete=models.CASCADE, related_name='attachment')