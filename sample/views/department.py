from utils.rest_framework.viewsets import AuditableModelViewSet

from ..models import Department
from ..serializers.department import DepartmentSerializer

class DepartmentViewSet(AuditableModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
