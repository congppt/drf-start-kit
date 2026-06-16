from huey.contrib import djhuey
from huey.signals import SIGNAL_CANCELED, SIGNAL_ERROR, SIGNAL_LOCKED, SIGNAL_REVOKED

from utils.log import logger

from .gc import *
from .token import *


@djhuey.signal(SIGNAL_ERROR, SIGNAL_LOCKED, SIGNAL_CANCELED, SIGNAL_REVOKED)
def task_not_executed_handler(signal, task_instance, exc=None):
    logger.opt(exception=exc).exception(
        f"Task {getattr(task_instance, 'name', task_instance.id)} not executed: {signal}"
    )
