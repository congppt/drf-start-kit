from rest_framework import viewsets

from .. import models
from .. import serializers
from .. import permissions

class GroupViewSet(viewsets.ModelViewSet):
    queryset = models.Group.objects.all()
    permission_classes = [permissions.DjangoModelPermissions, permissions.factory.permissions_class('auth.view_group')]
    serializer_class = serializers.GroupSerializer