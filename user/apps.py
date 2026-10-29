from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "user"

    def ready(self):
        from django.db.models.signals import post_migrate

        post_migrate.connect(_ensure_root_user_on_migrate, sender=self)


def _ensure_root_user_on_migrate(sender, using, **kwargs):
    if using != "default":
        return
    from user.services import ensure_root_user

    ensure_root_user()
