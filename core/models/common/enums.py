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