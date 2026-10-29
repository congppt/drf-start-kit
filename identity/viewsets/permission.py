from extensions import permissions
from rest_framework import viewsets

from core import mixins

from .. import models, serializers


class PermissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = models.Permission.objects.select_related("content_type").all()
    permission_classes = [permissions.permissions_class("auth.view_group")]
    serializer_class = serializers.PermissionSerializer
    pagination_class = None
