from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)

from .common import CreateAuditableModelMixin, DestroyAuditableModelMixin, UpdateAuditableModelMixin
