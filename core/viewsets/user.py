import django_filters
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .. import filters, mixins, models, pagination, permissions, serializers, throttling
from . import novel


class UserFilter(django_filters.FilterSet):
    groups = django_filters.ModelMultipleChoiceFilter(queryset=models.Group.objects.all())

    class Meta:
        model = models.User
        fields = ["is_active"]


class UserViewSet(
    mixins.CreateAuditableModelMixin,
    mixins.UpdateAuditableModelMixin,
    mixins.ChoiceListModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = models.User.objects.prefetch_related("attachments__file", "groups").all()
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    filterset_class = UserFilter
    pagination_class = pagination.factory.limit_offset_class(maximum_limit=200)
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "email", "created_at", "date_joined"]
    ordering = ["username"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.has_perm("core.view_user"):
            return queryset.filter(pk=user.pk)
        return queryset

    def get_serializer_class(self):
        match self.action:
            case "create":
                return serializers.UserCreateSerializer
            case "update" | "partial_update":
                return serializers.UserUpdateSerializer
            case "create_bookmark":
                return serializers.UserBookmarkCreateSerializer
            case _:
                return super().get_serializer_class()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return super().get_permissions()

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
            models.Permission.objects.select_related("content_type")
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
        throttle_classes=[throttling.factory.per_view_user_rate_throttle("10/minute")],
    )
    def change_password_self(self, request, pk=None):
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
        throttle_classes=[throttling.factory.per_view_user_rate_throttle("10/minute")],
    )
    def generate_avatar_upload_url_self(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["put"],
        url_path="me/avatar",
        serializer_class=serializers.UserAvatarSelfUpdateSerializer,
        permission_classes=[permissions.IsAuthenticated],
    )
    def change_avatar_self(self, request, pk=None):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(responses=serializers.NovelListSerializer(many=True))
    @action(
        detail=False,
        methods=["get"],
        url_path="me/novels",
        serializer_class=serializers.NovelListSerializer,
        permission_classes=[permissions.IsAuthenticated],
        pagination_class=pagination.Max100LimitOffsetPagination,
        filterset_class=novel.NovelFilter,
        search_fields = ["title", "blurb"],
        ordering_fields=["created_at", "last_publication_at"],
        ordering=["-last_publication_at"],
    )
    def list_novels(self, request, pk=None):
        queryset = self.filter_queryset(
            models.Novel.objects.select_related("author")
            .prefetch_related("genres", "attachments__file")
            .filter(author=request.user)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(responses=serializers.UserReadingProgressSerializer(many=True))
    @action(
        detail=False,
        methods=["get"],
        url_path="me/reading-progresses",
        serializer_class=serializers.UserReadingProgressSerializer,
        permission_classes=[permissions.IsAuthenticated],
        pagination_class=pagination.Max100LimitOffsetPagination,
        filter_backends=[filters.OrderingFilter],
        ordering_fields=["updated_at"],
        ordering=["-updated_at"],
    )
    def list_reading_progresses(self, request, pk=None):
        queryset = self.filter_queryset(
            models.ReadingProgress.objects.select_related("novel", "chapter")
            .filter(user=request.user)
            .exclude(Q(novel__status=models.NovelStatus.DRAFT) | Q(chapter__is_published=False))
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(responses=serializers.UserBookmarkSerializer(many=True))
    @action(
        detail=False,
        methods=["get"],
        url_path="me/bookmarks",
        serializer_class=serializers.UserBookmarkSerializer,
        permission_classes=[permissions.IsAuthenticated],
        pagination_class=pagination.Max100LimitOffsetPagination,
        filter_backends=[filters.OrderingFilter],
        ordering_fields=["created_at"],
        ordering=["-created_at"],
    )
    def list_bookmarks(self, request, pk=None):
        queryset = self.filter_queryset(
            models.Bookmark.objects.select_related("novel__author")
            .prefetch_related("novel__genres", "novel__attachments__file")
            .filter(user=request.user)
            .exclude(novel__status=models.NovelStatus.DRAFT)
            .order_by("-created_at")
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(responses={201: serializers.UserBookmarkCreateSerializer})
    @list_bookmarks.mapping.post
    def create_bookmark(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[OpenApiParameter(name="id", description="Bookmark ID", location=OpenApiParameter.PATH, type=int)]
    )
    @action(
        detail=False,
        methods=["delete"],
        url_path=r"me/bookmarks/(?P<pk>\d+)",
        permission_classes=[permissions.IsAuthenticated, permissions.factory.object_permission_class("user")],
    )
    def destroy_bookmark(self, request, pk):
        instance: models.Bookmark = get_object_or_404(models.Bookmark.objects.filter(user=request.user), pk=pk)
        self.check_object_permissions(request, instance)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
