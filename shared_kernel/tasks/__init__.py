import os

from huey.contrib import djhuey
from huey.signals import SIGNAL_CANCELED, SIGNAL_ERROR, SIGNAL_LOCKED, SIGNAL_REVOKED

from utils.log import LOG_DIR, LOG_OPTS, LogLevel, logger

from .gc import *

logger.add(
    os.path.join(LOG_DIR, "{time:YY-MM-DD}.background.json"),
    level=LogLevel.INFO,
    filter=lambda record: "tasks" in record["name"].lower(),
    **LOG_OPTS,
)


@djhuey.signal(SIGNAL_ERROR, SIGNAL_LOCKED, SIGNAL_CANCELED, SIGNAL_REVOKED)
def task_not_executed_handler(signal, task_instance, exc=None):
    logger.opt(exception=exc).exception(
        f"Task {getattr(task_instance, 'name', task_instance.id)} not executed: {signal}"
    )
