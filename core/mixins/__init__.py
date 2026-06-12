from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, DestroyModelMixin, RetrieveModelMixin, ListModelMixin

from .common import CreateAuditableModelMixin, UpdateAuditableModelMixin, DestroyAuditableModelMixin

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