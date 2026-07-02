import contextlib

import django_filters
from django.db.models import Q, Value
from django.db.models.functions import Concat
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
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
            case "create" | "update" | "partial_update":
                return serializers.NovelInputSerializer
            case "retrieve_reading_progress":
                return serializers.NovelReadingProgressSerializer
            case "update_reading_progress":
                return serializers.NovelReadingProgressInputSerializer
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["novel_id"] = None
        with contextlib.suppress(KeyError):
            context["novel_id"] = int(self.kwargs["pk"])
        return context

    @action(
        detail=True,
        methods=["post"],
        url_path="cover/presigned-upload-url",
        serializer_class=serializers.NovelCoverUploadUrlSerializer,
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
        serializer_class=serializers.NovelCoverUpdateSerializer,
    )
    def change_cover(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["get"],
        url_path="reading-progress",
        permission_classes=[permissions.IsAuthenticated],
    )
    def retrieve_reading_progress(self, request, pk=None):
        instance = get_object_or_404(
            models.ReadingProgress.objects.select_related("novel", "chapter")
            .filter(user=request.user, novel_id=pk)
            .exclude(Q(novel__status=models.NovelStatus.DRAFT) | Q(chapter__is_published=False))
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @retrieve_reading_progress.mapping.put
    def update_reading_progress(self, request, pk=None):
        instance = models.ReadingProgress.objects.filter(user=request.user, novel_id=pk).first()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, novel_id=pk)
        return Response(serializer.data)
