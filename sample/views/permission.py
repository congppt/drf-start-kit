from django.contrib.auth.models import Permission
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets, permissions, mixins
from rest_framework_extensions.mixins import NestedViewSetMixin

from ..serializers.permission import PermissionSerializer

class PermissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Permission.objects.select_related('content_type').all()
    permission_classes = [permissions.DjangoModelPermissions]
    serializer_class = PermissionSerializer
    pagination_class = None

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name='parent_lookup_group',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Group ID',
            ),
        ],
    ),
)
class GroupPermissionViewSet(NestedViewSetMixin, PermissionViewSet):
    pass