from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from .. import common


class _UserManager(common.AuditableManager, BaseUserManager):
    def _create_user(self, username, email, password, **extra_fields):
        performed_by = extra_fields.pop("performed_by", None)
        user = self._create_user_object(username, email, password, **extra_fields)
        user.save(performed_by=performed_by, using=self._db)
        return user

    async def _acreate_user(self, username, email, password, **extra_fields):
        performed_by = extra_fields.pop("performed_by", None)
        user = self._create_user_object(username, email, password, **extra_fields)
        await user.asave(performed_by=performed_by, using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        from ...constants import SYSTEM_ACTOR

        extra_fields.setdefault("performed_by", SYSTEM_ACTOR)
        return super().create_superuser(username, email, password, **extra_fields)

    async def acreate_superuser(self, username, email=None, password=None, **extra_fields):
        from ...constants import SYSTEM_ACTOR

        extra_fields.setdefault("performed_by", SYSTEM_ACTOR)
        return await super().acreate_superuser(username, email, password, **extra_fields)


class User(common.AuditableModel, AbstractUser):
    objects = _UserManager()

    preferences = models.JSONField(default=dict)
    attachments = GenericRelation(common.FileAttachment)

    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"
        db_table = "user"

    AVATAR_FIELD_NAME = "avatar"
    AVATAR_IS_PUBLIC = True
