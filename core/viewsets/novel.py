import contextlib

import django_filters
from django.db.models import Case, Count, Exists, F, IntegerField, OuterRef, Q, Value, When
from django.db.models.functions import Concat
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .. import filters, mixins, models, pagination, permissions, serializers, throttling
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
    serializer_class = serializers.NovelListSerializer
    filterset_class = NovelFilter
    search_fields = ["title", "blurb", "author_name"]
    ordering_fields = ["read_count", "weekly_read_count", "created_at"]

    def get_serializer_class(self):
        match self.action:
            case "create" | "update" | "partial_update":
                return serializers.NovelInputSerializer
            case "update_reading_progress":
                return serializers.NovelReadingProgressInputSerializer
            case "retrieve":
                return serializers.NovelDetailSerializer
            case _:
                return super().get_serializer_class()

    def _annotate_read_stats(self, queryset):
        since_week = timezone.now() - timezone.timedelta(days=7)
        return queryset.annotate(
            read_count=Count("read_events"),
            weekly_read_count=Count(
                "read_events",
                filter=Q(read_events__created_at__gte=since_week),
            ),
        )

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if self.action in {"retrieve", "list_suggestions"}:
            queryset = self._annotate_read_stats(queryset)
            if self.action == "retrieve":
                queryset = queryset.annotate(
                    has_bookmark=Exists(models.Bookmark.objects.filter(user=user, novel=OuterRef("pk"))),
                )
        if user.has_perm("core.view_novel"):
            return queryset
        if user.is_authenticated and self.detail:
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
        throttle_classes=[throttling.factory.per_view_user_rate_throttle("10/minute")],
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
        serializer_class=serializers.NovelReadingProgressSerializer,
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

    @extend_schema(responses=serializers.NovelSuggestionSerializer(many=True))
    @action(
        detail=False,
        methods=["get"],
        url_path="suggestions",
        serializer_class=serializers.NovelSuggestionSerializer,
        permission_classes=[permissions.AllowAny],
        pagination_class=pagination.Max100LimitOffsetPagination,
        filter_backends=[],
    )
    def list_suggestions(self, request):
        SUGGESTION_WEEKLY_READ_WEIGHT = 7
        SUGGESTION_READ_COUNT_WEIGHT = 2
        SUGGESTION_RECENCY_RECENT_SCORE = 10
        SUGGESTION_RECENCY_MONTH_SCORE = 5
        since_week = timezone.now() - timezone.timedelta(days=7)
        since_month = timezone.now() - timezone.timedelta(days=30)
        queryset = (
            self.get_queryset()
            .annotate(
                recency_score=Case(
                    When(last_publication_at__gte=since_week, then=Value(SUGGESTION_RECENCY_RECENT_SCORE)),
                    When(last_publication_at__gte=since_month, then=Value(SUGGESTION_RECENCY_MONTH_SCORE)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                suggestion_score=(
                    F("weekly_read_count") * Value(SUGGESTION_WEEKLY_READ_WEIGHT)
                    + F("read_count") * Value(SUGGESTION_READ_COUNT_WEIGHT)
                    + F("recency_score")
                ),
            )
            .order_by("-suggestion_score", "-weekly_read_count")
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
