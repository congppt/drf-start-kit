from rest_framework import viewsets

from .. import mixins, models, permissions, serializers


class GroupViewSet(mixins.ChoiceListModelMixin, viewsets.ModelViewSet):
    queryset = models.Group.objects.all()
    permission_classes = [permissions.DjangoModelPermissions, permissions.factory.permissions_class("auth.view_group")]
    serializer_class = serializers.GroupSerializer
