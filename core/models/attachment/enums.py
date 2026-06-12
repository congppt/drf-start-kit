from django.db import models

class UploadStatus(models.TextChoices):
    PENDING = 'pending'
    READY = 'ready'