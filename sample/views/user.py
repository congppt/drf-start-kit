from django.contrib.auth.models import User, Group
import django_filters
from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from ..serializers.user import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserSelfUpdateSerializer,
    PasswordChangeSerializer,
    PasswordSelfChangeSerializer,
    UserAvatarSelfUpdateSerializer,
    UserAvatarUploadUrlSerializer
)
from utils.rest_framework.permissions import permissions_class_factory
from utils.rest_framework import pagination

class UserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains')
    groups = django_filters.ModelMultipleChoiceFilter(queryset=Group.objects.all())

    class Meta:
        model = User
        fields = ['is_active']

class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.select_related('detail').prefetch_related('detail__attachments__file').all()
    permission_classes = [permissions.DjangoModelPermissions]
    filterset_class = UserFilter
    pagination_class = pagination.limit_offset_class_factory(maximum_limit=100)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action in ['update_self', 'partial_update_self']:
            return UserSelfUpdateSerializer
        if self.action == 'change_password':
            return PasswordChangeSerializer
        if self.action == 'change_password_self':
            return PasswordSelfChangeSerializer
        if self.action == 'generate_avatar_upload_url_self':
            return UserAvatarUploadUrlSerializer
        if self.action == 'change_avatar_self':
            return UserAvatarSelfUpdateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(performed_by=self.request.user)

    @action(detail=False, methods=['patch'], url_path='me')
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
        permission_classes=[
            permissions.DjangoModelPermissions,
            permissions_class_factory('sample.change_user_detail')
        ]
    )
    def change_password(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response()

    @action(detail=False, methods=['put'], url_path='me/password')
    def change_password_self(self, request, pk=None):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response()

    @action(detail=False, methods=['post'], url_path='me/avatar/presigned-upload-url', permission_classes=[permissions.IsAuthenticated])
    def generate_avatar_upload_url_self(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put'], url_path='me/avatar')
    def change_avatar_self(self, request, pk=None):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response()