from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, UpdateModelMixin


class CreateAuditableModelMixin(CreateModelMixin):
    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)


class UpdateAuditableModelMixin(UpdateModelMixin):
    def perform_update(self, serializer):
        serializer.save(performed_by=self.request.user)


class DestroyAuditableModelMixin(DestroyModelMixin):
    def perform_destroy(self, instance):
        instance.delete(performed_by=self.request.user)
