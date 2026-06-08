from typing import TYPE_CHECKING
from django.db import models
from django.contrib.auth.models import User

from utils.django.models.audit import AuditableMixin

if TYPE_CHECKING:
    from .user_detail import UserDetail
else:
    UserDetail = 'UserDetail'


class Department(AuditableMixin, models.Model):
    slug = models.SlugField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    users = models.ManyToManyField(
        User,
        through=UserDetail,
        related_name='departments',
    )

    def __str__(self):
        return self.name