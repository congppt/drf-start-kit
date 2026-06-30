from .. import mixins, models, permissions, serializers
from .common.audit import AuditableModelViewSet


class NovelChapterViewSet(mixins.NestedViewSetMixin, mixins.ChoiceListModelMixin, AuditableModelViewSet):
    queryset = models.Chapter.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
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
        return context

    def perform_create(self, serializer):
        serializer.save(novel_id=serializer.context["novel_id"], performed_by=self.request.user)
