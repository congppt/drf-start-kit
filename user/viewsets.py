from django.db.models import Q
from extensions import filters, mixins, pagination, permissions, throttling
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from identity.models import Group, Permission
from shared_kernel.mixins import CreateAuditableModelMixin, UpdateAuditableModelMixin

from . import serializers
from .models import User


class UserFilter(filters.FilterSet):
    groups = filters.ModelMultipleChoiceFilter(queryset=Group.objects.all())

    class Meta:
        model = User
        fields = ["is_active"]


class UserViewSet(
    CreateAuditableModelMixin,
    UpdateAuditableModelMixin,
    mixins.ChoiceListModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = User.objects.prefetch_related("attachments__file", "groups").all()
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    filterset_class = UserFilter
    pagination_class = pagination.limit_offset_class(maximum_limit=200)
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "email", "created", "date_joined"]
    ordering = ["username"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.has_perm("user.view_user"):
            return queryset.filter(pk=user.pk)
        return queryset

    def get_serializer_class(self):
        match self.action:
            case "create":
                return serializers.UserCreateSerializer
            case "update" | "partial_update":
                return serializers.UserUpdateSerializer
            case _:
                return super().get_serializer_class()

    @action(
        detail=False,
        methods=["patch"],
        url_path="me",
        serializer_class=serializers.UserSelfUpdateSerializer,
        permission_classes=[permissions.IsAuthenticated],
    )
    def update_self(self, request, pk=None):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        serializer_class=serializers.UserSelfSerializer,
        permission_classes=[permissions.IsAuthenticated],
    )
    def retrieve_self(self, request):
        instance = request.user
        instance_perms = (
            Permission.objects.select_related("content_type")
            .filter(Q(user=instance) | Q(group__user=instance))
            .distinct()
        )
        serializer = self.get_serializer({"user": instance, "permissions": instance_perms})
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["put"],
        url_path="password",
        serializer_class=serializers.PasswordChangeSerializer,
    )
    def change_password(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["put"],
        url_path="me/password",
        serializer_class=serializers.PasswordSelfChangeSerializer,
        permission_classes=[permissions.IsAuthenticated],
        throttle_classes=[throttling.scoped_rate_throttle("10/minute", "change_personal_password")],
    )
    def change_personal_password(self, request, pk=None):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["post"],
        url_path="me/avatar/presigned-upload-url",
        serializer_class=serializers.UserAvatarUploadUrlSerializer,
        permission_classes=[permissions.IsAuthenticated],
        throttle_classes=[throttling.scoped_rate_throttle("10/minute", "avatar_upload")],
    )
    def generate_personal_avatar_upload_url(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(serializer.data)
