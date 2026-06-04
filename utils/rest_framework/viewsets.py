from rest_framework import viewsets, permissions

class AuditableModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(performed_by=self.request.user)
    
    def perform_destroy(self, instance):
        instance.delete(performed_by=self.request.user)