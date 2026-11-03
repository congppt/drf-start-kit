from django.utils import timezone

from user.models import User

from .models import Notification


def mark_as_read(notification: Notification):
    if notification.is_read:
        return notification
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=["is_read", "read_at"])
    return notification

def mark_all_as_read(user: User):
    queryset = Notification.objects.filter(recipient=user, is_read=False)
    queryset.update(is_read=True, read_at=timezone.now())
    return