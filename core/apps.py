from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from django.db.models.signals import post_migrate

        post_migrate.connect(_ensure_root_user_on_migrate, sender=self)

def _ensure_root_user_on_migrate(sender, using, **kwargs):
    if using != "default":
        return
    from core.services.user import ensure_root_user

    ensure_root_user()