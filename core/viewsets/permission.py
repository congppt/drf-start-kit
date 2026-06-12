from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from .. import models
from .. import serializers
from .. import mixins
from .. import permissions

class PermissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = models.Permission.objects.select_related('content_type').all()
    permission_classes = [permissions.factory.permissions_class('auth.view_group')]
    serializer_class = serializers.PermissionSerializer
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

class UserPermissionViewSet(NestedViewSetMixin, PermissionViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pass