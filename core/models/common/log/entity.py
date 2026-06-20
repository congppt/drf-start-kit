from django.db import models

from .enums import LogLevel


class LogEntry(models.Model):
    id = models.UUIDField(primary_key=True)
    timestamp = models.DateTimeField(db_index=True)
    level = models.PositiveSmallIntegerField(choices=LogLevel.choices, db_index=True)
    message = models.TextField(blank=True)
    extra = models.JSONField(default=dict)

    class Meta:
        db_table = "log_entry"
