import os
import sys
from datetime import timedelta
from enum import IntEnum

import env
from loguru import logger as __logger
from loguru._defaults import (
    LOGURU_CRITICAL_NO,
    LOGURU_DEBUG_NO,
    LOGURU_ERROR_NO,
    LOGURU_INFO_NO,
    LOGURU_SUCCESS_NO,
    LOGURU_TRACE_NO,
    LOGURU_WARNING_NO,
)


class LogLevel(IntEnum):
    TRACE = LOGURU_TRACE_NO
    DEBUG = LOGURU_DEBUG_NO
    INFO = LOGURU_INFO_NO
    SUCCESS = LOGURU_SUCCESS_NO
    WARNING = LOGURU_WARNING_NO
    ERROR = LOGURU_ERROR_NO
    CRITICAL = LOGURU_CRITICAL_NO


LOG_DIR = "logs"
# Set traceback limit
sys.tracebacklimit = 1
# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)
# Remove default handler
__logger.remove(0)
# Default log options
LOG_OPTS = dict(
    rotation=timedelta(days=1),
    retention=timedelta(days=env.LOG_RETENTION),
    enqueue=True,
    format="{message}",
    encoding="utf-8",
    serialize=True,
)

# Standard logger
__logger.add(
    os.path.join(LOG_DIR, "{time:YY-MM-DD}.json"),
    level=LogLevel.INFO,
    **LOG_OPTS,
)

# Error logger
__logger.add(
    os.path.join(LOG_DIR, "{time:YY-MM-DD}.error.json"),
    level=LogLevel.ERROR,
    **LOG_OPTS,
)

#  Console logger
__logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{module}.{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> {extra}",
    level=LogLevel.TRACE if not env.IS_PRODUCTION else LogLevel.INFO,
    enqueue=True,
)

logger = __logger
