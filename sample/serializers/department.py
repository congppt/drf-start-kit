from utils.rest_framework.serializer import ExcludeDeleteFieldsSerializer

from ..models import Department

class DepartmentSerializer(ExcludeDeleteFieldsSerializer):

    class Meta:
        model = Department
        exclude = ['users']