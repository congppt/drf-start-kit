import django_filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .. import models
from .. import serializers
from .. import mixins
from .. import permissions
from .. import pagination


class UserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains')
    groups = django_filters.ModelMultipleChoiceFilter(queryset=models.Group.objects.all())

    class Meta:
        model = models.User
        fields = ['is_active']

class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = models.User.objects.prefetch_related('attachments__file').all()
    permission_classes = [permissions.DjangoModelPermissions]
    filterset_class = UserFilter
    pagination_class = pagination.factory.limit_offset_class(maximum_limit=100)

    def get_serializer_class(self):
        match self.action:
            case 'create':
                return serializers.UserCreateSerializer
            case 'update' | 'partial_update':
                return serializers.UserUpdateSerializer
            case 'update_self' | 'partial_update_self':
                return serializers.UserSelfUpdateSerializer
            case 'change_password':
                return serializers.PasswordChangeSerializer
            case 'change_password_self':
                return serializers.PasswordSelfChangeSerializer
            case 'generate_avatar_upload_url_self':
                return serializers.UserAvatarUploadUrlSerializer
            case 'change_avatar_self':
                return serializers.UserAvatarSelfUpdateSerializer
            case _:
                return serializers.UserSerializer

    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(performed_by=self.request.user)

    @action(
        detail=False,
        methods=['patch'],
        url_path='me',
        permission_classes=[permissions.IsAuthenticated]
    )
    def update_self(self, request, pk=None):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['put'],
        url_path='password',
    )
    def change_password(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response()

    @action(
        detail=False,
        methods=['put'],
        url_path='me/password',
        permission_classes=[permissions.IsAuthenticated]
    )
    def change_password_self(self, request, pk=None):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response()

    @action(
        detail=False,
        methods=['post'],
        url_path='me/avatar/presigned-upload-url',
        permission_classes=[permissions.IsAuthenticated]
    )
    def generate_avatar_upload_url_self(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[permissions.IsAuthenticated]
    )
    def change_avatar_self(self, request, pk=None):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response()