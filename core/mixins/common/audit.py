class CreateAuditableModelMixin:
    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)


class UpdateAuditableModelMixin:
    def perform_update(self, serializer):
        serializer.save(performed_by=self.request.user)


class DestroyAuditableModelMixin:
    def perform_destroy(self, instance):
        instance.delete(performed_by=self.request.user)
