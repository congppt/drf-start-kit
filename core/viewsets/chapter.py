from django.db.models import Q

from .. import mixins, models, permissions, serializers
from .common.audit import AuditableModelViewSet


class NovelChapterViewSet(mixins.NestedViewSetMixin, mixins.ChoiceListModelMixin, AuditableModelViewSet):
    queryset = models.Chapter.objects.select_related("novel__author").all()
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
        if user.is_authenticated:
            return queryset.filter(
                Q(novel__author=user) | (Q(is_published=True) & ~Q(novel__status=models.NovelStatus.DRAFT))
            )
        return queryset.exclude(novel__status=models.NovelStatus.DRAFT).filter(is_published=True)

    def perform_create(self, serializer):
        serializer.save(novel_id=serializer.context["novel_id"], performed_by=self.request.user)
