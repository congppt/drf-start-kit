from django.conf import settings

from . import models


class LogDBRouter:
    def owns_model(self, model) -> bool:
        return model._meta.concrete_model in [models.LogEntry]

    def db_for_read(self, model, **hints):
        if self.owns_model(model):
            return settings.LOG_DB
        return None

    def db_for_write(self, model, **hints):
        if self.owns_model(model):
            return settings.LOG_DB
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if self.owns_model(obj1._meta.model) and self.owns_model(obj2._meta.model):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == models.LogEntry._meta.app_label and model_name == models.LogEntry._meta.model_name:
            return db == settings.LOG_DB
        if db == settings.LOG_DB:
            return False
        return None
