from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from ..serializers.user import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserSelfUpdateSerializer,
    SuperUserPasswordChangeSerializer,
    PasswordSelfChangeSerializer
)

class UserViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = User.objects.select_related('detail').all()
    permission_classes = [permissions.DjangoModelPermissions]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action in ['update_self', 'partial_update_self']:
            return UserSelfUpdateSerializer
        if self.action == 'change_password':
            return SuperUserPasswordChangeSerializer
        if self.action == 'change_password_self':
            return PasswordSelfChangeSerializer
        return UserSerializer

    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(performed_by=self.request.user)

    @action(detail=False, methods=['patch'], url_path='me')
    def update_self(self, request, pk=None):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='password')
    def change_password(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response()

    @action(detail=False, methods=['patch'], url_path='me/password')
    def change_password_self(self, request, pk=None):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response()