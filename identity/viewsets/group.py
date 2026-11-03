from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets

from extensions import mixins, permissions

from .. import models, serializers
from .permission import PermissionViewSet


class GroupViewSet(mixins.ChoiceListModelMixin, viewsets.ModelViewSet):
    queryset = models.Group.objects.all()
    permission_classes = [permissions.DjangoModelPermissions, permissions.permissions_class("auth.view_group")]
    serializer_class = serializers.GroupSerializer
    search_fields = ["name"]


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="parent_group",
            type=int,
            location=OpenApiParameter.PATH,
            description="Group ID",
        ),
    ],
)
class GroupPermissionViewSet(mixins.NestedViewSetMixin, PermissionViewSet):
    pass
