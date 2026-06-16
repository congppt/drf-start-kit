from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)

from .common import CreateAuditableModelMixin, DestroyAuditableModelMixin, UpdateAuditableModelMixin

__all__ = [
    # DRF Built-in Mixins
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    RetrieveModelMixin,
    ListModelMixin,
    # Auditable Model Based Mixins
    CreateAuditableModelMixin,
    UpdateAuditableModelMixin,
    DestroyAuditableModelMixin,
    #
]
