from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from shared_kernel.models import audit

_SYS_CREATE_SUPERUSER = audit.SystemActor("user", "create-superuser")


class _UserManager(audit.AuditableManager, BaseUserManager):
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
        extra_fields.setdefault("performed_by", _SYS_CREATE_SUPERUSER)
        return super().create_superuser(username, email, password, **extra_fields)

    async def acreate_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("performed_by", _SYS_CREATE_SUPERUSER)
        return await super().acreate_superuser(username, email, password, **extra_fields)


class User(audit.AuditableModel, AbstractUser):
    objects = _UserManager()

    # AbstractUser.username is unique for every row. Active accounts keep that
    # rule through a partial unique constraint; a soft-deleted row may share
    # its username with a new account.
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=False,
        help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    avatar = models.ForeignKey(
        "attachment.FileAsset",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    preferences = models.JSONField(default=dict)

    class Meta(AbstractUser.Meta):
        abstract = False
        swappable = "AUTH_USER_MODEL"
        db_table = "app_user"
        constraints = [
            models.UniqueConstraint(
                fields=["username"],
                condition=models.Q(is_deleted=False),
                name="uq_user_username_when_active",
                violation_error_message=_("A user with that username already exists."),
            ),
            models.UniqueConstraint(
                Lower("email"),
                condition=models.Q(is_deleted=False) & ~models.Q(email=""),
                name="uq_user_email_ci_when_set",
            ),
            models.UniqueConstraint(
                fields=["avatar"],
                condition=models.Q(avatar__isnull=False),
                name="uq_user_avatar",
            ),
        ]

    def __str__(self) -> str:
        full_name = self.get_full_name()
        if full_name:
            return f"{full_name} ({self.username})"
        return self.username

    AVATAR_IS_PUBLIC = True
