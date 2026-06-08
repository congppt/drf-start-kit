from django.contrib.auth.models import Permission
from rest_framework import viewsets, permissions, mixins

from ..serializers.permission import PermissionSerializer

class PermissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Permission.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    serializer_class = PermissionSerializer
    pagination_class = None