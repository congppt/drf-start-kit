from rest_framework import viewsets

from .. import mixins, models, permissions, serializers


class PermissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = models.Permission.objects.select_related("content_type").all()
    permission_classes = [permissions.factory.permissions_class("auth.view_group")]
    serializer_class = serializers.PermissionSerializer
    pagination_class = None



