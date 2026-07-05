import uuid

from django.db.models import BooleanField, Case, Exists, OuterRef, Q, Value, When
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import Http404

from .. import mixins, models, permissions, serializers, throttling
from .common.audit import AuditableModelViewSet

VIEWER_ID_COOKIE = "viewer_id"
VIEWER_ID_COOKIE_MAX_AGE = models.NovelReadEvent.CREATE_RESTRICTED_SECONDS


class NovelChapterViewSet(mixins.NestedViewSetMixin, mixins.ChoiceListModelMixin, AuditableModelViewSet):
    queryset = models.Chapter.objects.select_related("novel__author").annotate(is_unlocked=Value(True)).all()
    permission_classes = [permissions.NovelChapterPermission]
    serializer_class = serializers.ChapterListSerializer
    ordering_fields = ["lexorank"]
    ordering = ["-lexorank"]

    def get_serializer_class(self):
        match self.action:
            case "retrieve":
                return serializers.ChapterDetailSerializer
            case "create" | "update" | "partial_update":
                return serializers.ChapterInputSerializer
            case _:
                return super().get_serializer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["novel_id"] = int(self.kwargs["novel_id"])
        context["visible_chapters_qs"] = self.get_queryset()
        return context

    def get_queryset(self):
        # Get novel filtered queryset thanks to the nested viewset mixin
        queryset = super().get_queryset()
        user = self.request.user
        if user.has_perm("core.view_chapter"):
            return queryset
        if not user.is_authenticated:
            return (
                queryset.annotate(
                    is_unlocked=Case(
                        When(price=0, then=Value(True)),
                        default=Value(False),
                    )
                )
                .exclude(novel__status=models.NovelStatus.DRAFT)
                .filter(is_published=True)
            )
        queryset = queryset.annotate(
            is_unlocked=Case(
                When(price=0, then=Value(True)),
                When(novel__author=user, then=Value(True)),
                default=Exists(models.ChapterPurchase.objects.filter(user=user, chapter=OuterRef("pk"))),
                output_field=BooleanField(),
            )
        )
        return queryset.filter(
            Q(novel__author=user) | (Q(is_published=True) & ~Q(novel__status=models.NovelStatus.DRAFT))
        )

    def perform_create(self, serializer):
        serializer.save(novel_id=serializer.context["novel_id"], performed_by=self.request.user)

    @action(
        detail=True,
        methods=["post"],
        url_path="read-events",
        serializer_class=serializers.NovelReadEventSerializer,
        permission_classes=[permissions.AllowAny],
        throttle_classes=[
            throttling.factory.per_view_signed_cookie_rate_throttle(
                "1/minute", VIEWER_ID_COOKIE, VIEWER_ID_COOKIE_MAX_AGE
            ),
            throttling.factory.per_view_anon_rate_throttle("30/minute"),
        ],
    )
    def create_novel_read_event(self, request, novel_id=None, pk=None):
        chapter = self.get_object()
        if chapter.novel.status == models.NovelStatus.DRAFT or not chapter.is_published:
            raise Http404
        if request.user.is_authenticated:
            viewer_id = str(request.user.id)
        else:
            viewer_id = request.get_signed_cookie(VIEWER_ID_COOKIE, default=None, max_age=VIEWER_ID_COOKIE_MAX_AGE)
            if not viewer_id:
                response = Response(status=status.HTTP_204_NO_CONTENT)
                viewer_id = uuid.uuid4().hex
                response.set_signed_cookie(VIEWER_ID_COOKIE, viewer_id, httponly=True, max_age=VIEWER_ID_COOKIE_MAX_AGE)
                return response

        serializer = self.get_serializer(data={"novel": chapter.novel.pk, "viewer_id": viewer_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
