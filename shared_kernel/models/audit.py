import re

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import manager
from django.utils import timezone

_USERNAME_MAX_LENGTH = 150
_APP_LABEL_RE = re.compile(r"[a-z][a-z0-9_]*\Z")
_ACTION_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class SystemActor:
    """
    Audit actor for a write with no persisted user.

    ``username`` is ``system:{app}-{action}`` and is stored on ``created_by``,
    ``updated_by``, and ``deleted_by``. ``app`` is the Django app label. ``action``
    is the kebab-case name of that app's command, task, or consumer.
    """

    def __init__(self, app: str, action: str):
        if not isinstance(app, str) or _APP_LABEL_RE.fullmatch(app) is None:
            raise ValueError("app must be a Django app label")
        if not isinstance(action, str) or _ACTION_RE.fullmatch(action) is None:
            raise ValueError("action must be kebab-case")
        username = f"system:{app}-{action}"
        if len(username) > _USERNAME_MAX_LENGTH:
            raise ValueError(f"username must be at most {_USERNAME_MAX_LENGTH} characters")
        self.app = app
        self.action = action
        self.username = username


PerformedBy = SystemActor | AbstractUser


def _validate_performed_by(value: PerformedBy) -> PerformedBy:
    username = getattr(value, "username", None)
    if not isinstance(value, (SystemActor, AbstractUser)) or not isinstance(username, str) or not username:
        import sys

        caller = sys._getframe(1).f_code.co_name
        raise TypeError(
            f"{caller}() missing 1 required positional argument: "
            f"'performed_by' of type {SystemActor.__name__} or {AbstractUser.__name__}"
        )
    return value


class _AuditableQuerySet(models.QuerySet):
    def delete(self, performed_by: PerformedBy):
        performed_by = _validate_performed_by(performed_by)
        return super().update(is_deleted=True, deleted_at=timezone.now(), deleted_by=performed_by.username)

    def restore(self):
        return super().update(is_deleted=False, deleted_at=None, deleted_by=None)

    def update(self, **kwargs):
        actor = _validate_performed_by(kwargs.pop("performed_by"))
        return super().update(updated_by=actor.username, **kwargs)

    def bulk_update(self, *args, **kwargs):
        actor = _validate_performed_by(kwargs.pop("performed_by"))
        for obj in args[0]:
            obj.updated_by = actor.username
        return super().bulk_update(*args, **kwargs)

    def create(self, *args, **kwargs):
        """
        Create a new object with the given kwargs, saving it to the database
        and returning the created object.
        """
        actor = _validate_performed_by(kwargs.pop("performed_by"))
        reverse_one_to_one_fields = frozenset(kwargs).intersection(self.model._meta._reverse_one_to_one_field_names)
        if reverse_one_to_one_fields:
            raise ValueError(
                "The following fields do not exist in this model: %s" % ", ".join(reverse_one_to_one_fields)
            )

        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(performed_by=actor, force_insert=True, using=self.db)
        return obj

    def bulk_create(self, *args, **kwargs):
        actor = _validate_performed_by(kwargs.pop("performed_by"))
        for obj in args[0]:
            obj.created_by = actor.username
            obj.updated_by = actor.username
        return super().bulk_create(*args, **kwargs)


class AuditableManager(manager.BaseManager.from_queryset(_AuditableQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AuditableModel(models.Model):
    objects = AuditableManager()
    all_objects = models.Manager()

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=150, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=150, null=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True)
    deleted_by = models.CharField(max_length=150, null=True)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        actor = _validate_performed_by(kwargs.get("performed_by"))
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = actor.username
        self.save(update_fields=["is_deleted", "deleted", "deleted_by"], *args, **kwargs)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        super().save(update_fields=["is_deleted", "deleted", "deleted_by"])

    def save(self, *args, **kwargs):
        actor = _validate_performed_by(kwargs.pop("performed_by"))
        self.created_by = self.created_by or actor.username
        if not self.is_deleted:
            self.updated_by = actor.username
        return super().save(*args, **kwargs)
