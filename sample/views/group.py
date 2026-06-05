from django.contrib.auth.models import Group
from rest_framework import viewsets, permissions

from ..serializers.group import GroupSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    serializer_class = GroupSerializer