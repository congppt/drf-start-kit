from rest_framework import viewsets

from ... import mixins


class AuditableModelViewSet(
    mixins.CreateAuditableModelMixin,
    mixins.UpdateAuditableModelMixin,
    mixins.DestroyAuditableModelMixin,
    viewsets.ModelViewSet,
):
    pass
