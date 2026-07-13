from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets

from .. import mixins, models, permissions, serializers
from .permission import PermissionViewSet


class GroupViewSet(mixins.ChoiceListModelMixin, viewsets.ModelViewSet):
    queryset = models.Group.objects.all()
    permission_classes = [permissions.DjangoModelPermissions, permissions.factory.permissions_class("auth.view_group")]
    serializer_class = serializers.GroupSerializer
    search_fields = ["name"]


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="group_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="Group ID",
        ),
    ],
)
class GroupPermissionViewSet(mixins.NestedViewSetMixin, PermissionViewSet):
    pass
