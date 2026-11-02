from django.db import models


class Notification(models.Model):
    message = models.TextField()
    path = models.CharField(max_length=255, null=True)
    args = models.JSONField(default=dict)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        db_table = "app_notification"