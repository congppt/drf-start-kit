from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.log import LogLevel as LogLevelNo


class LogLevel(models.IntegerChoices):
    INFO = LogLevelNo.INFO.value, _("Info")
    SUCCESS = LogLevelNo.SUCCESS.value, _("Success")
    WARNING = LogLevelNo.WARNING.value, _("Warning")
    ERROR = LogLevelNo.ERROR.value, _("Error")
    CRITICAL = LogLevelNo.CRITICAL.value, _("Critical")

    @property
    def color(self) -> str:
        return {
            LogLevelNo.INFO: "#3B82F6",
            LogLevelNo.SUCCESS: "#22C55E",
            LogLevelNo.WARNING: "#EAB308",
            LogLevelNo.ERROR: "#EF4444",
            LogLevelNo.CRITICAL: "#A855F7",
        }[self]


class LogEntry(models.Model):
    id = models.UUIDField(primary_key=True)
    timestamp = models.DateTimeField(db_index=True)
    level = models.PositiveSmallIntegerField(choices=LogLevel.choices, db_index=True)
    message = models.TextField(blank=True)
    extra = models.JSONField(default=dict)

    class Meta:
        db_table = "log_entry"
