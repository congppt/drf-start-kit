import django_filters
from django.db.models import Q, Value
from django.db.models.functions import Concat
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from .. import mixins, models, permissions, serializers, throttling
from .common import AuditableModelViewSet


class NovelFilter(django_filters.FilterSet):
    genres = django_filters.ModelMultipleChoiceFilter(queryset=models.Genre.objects.all(), conjoined=True)

    class Meta:
        model = models.Novel
        fields = ["status"]


class NovelViewSet(mixins.ChoiceListModelMixin, AuditableModelViewSet):
    queryset = (
        models.Novel.objects.select_related("author")
        .prefetch_related("genres", "attachments__file")
        .annotate(author_name=Concat("author__first_name", Value(" "), "author__last_name"))
        .all()
    )
    permission_classes = [permissions.NovelPermission]
    serializer_class = serializers.NovelSerializer
    filterset_class = NovelFilter
    search_fields = ["title", "blurb", "author_name"]

    def get_serializer_class(self):
        match self.action:
            case "generate_cover_upload_url":
                return serializers.NovelCoverUploadUrlSerializer
            case "change_cover":
                return serializers.NovelCoverUpdateSerializer
            case "create" | "update" | "partial_update":
                return serializers.NovelInputSerializer
            case _:
                return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.has_perm("core.view_novel"):
            return queryset
        if user.is_authenticated:
            return queryset.filter(~Q(status=models.NovelStatus.DRAFT) | Q(author=user))
        return queryset.exclude(status=models.NovelStatus.DRAFT)

    @action(
        detail=True,
        methods=["post"],
        url_path="cover/presigned-upload-url",
        throttle_classes=[throttling.factory.user_rate_throttle("10/minute")],
    )
    def generate_cover_upload_url(self, request, pk=None):
        # Check if the user has permission to change the novel
        _ = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["put"],
        url_path="cover",
    )
    def change_cover(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
