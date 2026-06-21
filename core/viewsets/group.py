from rest_framework import viewsets

from .. import models, permissions, serializers


class GroupViewSet(viewsets.ModelViewSet):
    queryset = models.Group.objects.all()
    permission_classes = [permissions.DjangoModelPermissions, permissions.factory.permissions_class("auth.view_group")]
    serializer_class = serializers.GroupSerializer

    def get_serializer_class(self):
        if self.request.query_params.get("for") == "options":
            return serializers.GroupChoicesSerializer
        return serializers.GroupSerializer
