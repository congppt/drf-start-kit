from django.utils import timezone
from huey import crontab
from huey.contrib import djhuey
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from utils.log import logger


@djhuey.db_periodic_task(crontab(minute="30", hour="3"))
@djhuey.lock_task("flush-expired-tokens")
def flush_expired_tokens():
    logger.info("Starting expired JWT token cleanup")
    deleted_count, _ = OutstandingToken.objects.filter(
        expires_at__lt=timezone.now(),
    ).delete()
    logger.info("Expired JWT token cleanup completed", extra={"deleted_count": deleted_count})
    return deleted_count
