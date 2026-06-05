from django.contrib.auth.models import Permission
from rest_framework import viewsets, permissions, mixins

from ..serializers.permission import PermissionSerializer

class PermissionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Permission.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PermissionSerializer