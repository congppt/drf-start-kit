from django.contrib.auth.models import User
from django.db import models
from django.db.models import manager
from django.utils import timezone

class AuditableQuerySet(models.QuerySet):
    def delete(self, performed_by: User):
        if not isinstance(performed_by, User):
            raise TypeError(f"'performed_by' parameter must be of type {User.__name__}")
        return super().update(
            is_deleted=True,
            deleted=timezone.now(),
            deleted_by=performed_by.username
        )

    def restore(self):
        return super().update(
            is_deleted=False,
            deleted=None,
            deleted_by=None
        )

    def update(self, **kwargs):
        user = kwargs.pop('performed_by')
        if not user or not isinstance(user, User):
            raise TypeError(f"update() missing 1 required positional argument: 'performed_by' of type {User.__name__}")
        return super().update(
            updated_by=user.username,
            **kwargs
        )

    def bulk_update(self, *args, **kwargs):
        user = kwargs.pop('performed_by')
        if not user or not isinstance(user, User):
            raise TypeError(f"bulk_update() missing 1 required positional argument: 'performed_by' of type {User.__name__}")
        for obj in args[0]:
            obj.updated_by = user.username
        return super().bulk_update(*args, **kwargs)

    def create(self, *args, **kwargs):
        """
        Create a new object with the given kwargs, saving it to the database
        and returning the created object.
        """
        user = kwargs.pop('performed_by')
        if not user or not isinstance(user, User):
            raise TypeError(f"create() missing 1 required positional argument: 'performed_by' of type {User.__name__}")
        reverse_one_to_one_fields = frozenset(kwargs).intersection(
            self.model._meta._reverse_one_to_one_field_names
        )
        if reverse_one_to_one_fields:
            raise ValueError(
                "The following fields do not exist in this model: %s"
                % ", ".join(reverse_one_to_one_fields)
            )

        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(performed_by=user, force_insert=True, using=self.db)
        return obj

    def bulk_create(self, *args, **kwargs):
        user = kwargs.pop('performed_by')
        if not user or not isinstance(user, User):
            raise TypeError(f"bulk_create() missing 1 required positional argument: 'performed_by' of type {User.__name__}")
        for obj in args[0]:
            obj.created_by = user.username
            obj.updated_by = user.username
        return super().bulk_create(*args, **kwargs)


class AuditableManager(manager.BaseManager.from_queryset(AuditableQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class AuditableMixin(models.Model):
    objects = AuditableManager()
    all_objects = models.Manager()

    created = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=150, null=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=150, null=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted = models.DateTimeField(null=True)
    deleted_by = models.CharField(max_length=150, null=True)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        user = kwargs.get('performed_by')
        if not user or not isinstance(user, User):
            raise TypeError(f"delete() missing 1 required positional argument: 'performed_by' of type {User.__name__}")
        self.deleted = timezone.now()
        self.deleted_by = user.username
        self.save(updated_fields=['is_deleted', 'deleted', 'deleted_by'], *args, **kwargs)

    def restore(self):
        self.is_deleted = False
        self.deleted = None
        self.deleted_by = None
        super().save(updated_fields=['is_deleted', 'deleted', 'deleted_by'])

    def save(self, *args, **kwargs):
        user = kwargs.pop('performed_by')
        if not user or not isinstance(user, User):
            raise TypeError(f"save() missing 1 required positional argument: 'performed_by' of type {User.__name__}")
        self.created_by = self.created_by or user.username
        if not self.is_deleted:
            self.updated_by = user.username
        return super().save(*args, **kwargs)
