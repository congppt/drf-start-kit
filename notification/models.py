from django.db import models
from django.utils.translation import gettext_lazy as _

from extensions.models import TextChoiceField
from user.models import User


class NotificationCategory(models.TextChoices):
    NORMAL = "normal", _("Normal")
    ALERT = "alert", _("Alert")
    REMINDER = "reminder", _("Reminder")


class Notification(models.Model):
    category = TextChoiceField(choices=NotificationCategory.choices, default=NotificationCategory.NORMAL)
    message = models.TextField()
    path = models.CharField(max_length=255, null=True)
    args = models.JSONField(default=dict)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "app_notification"
