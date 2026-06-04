from django.contrib.auth.models import User
from django.db import models

from .department import Department
from .auditable import AuditableMixin

class UserDetail(AuditableMixin, models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='detail')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
