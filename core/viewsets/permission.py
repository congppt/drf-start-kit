from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets

from .. import mixins, models, permissions, serializers


class PermissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = models.Permission.objects.select_related("content_type").all()
    permission_classes = [permissions.factory.permissions_class("auth.view_group")]
    serializer_class = serializers.PermissionSerializer
    pagination_class = None


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="group_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="Group ID",
        ),
    ],
)
class GroupPermissionViewSet(mixins.NestedViewSetMixin, PermissionViewSet):
    pass
