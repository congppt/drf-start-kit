from utils.rest_framework.viewsets import AuditableModelViewSet
from rest_framework import permissions

from ..models import Department
from ..serializers.department import DepartmentSerializer

class DepartmentViewSet(AuditableModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.DjangoModelPermissions]
