from ...serializers import ChoiceSerializer


class ChoiceListModelMixin:
    def get_serializer_class(self):
        if self.request.query_params.get("for") == "options":
            return getattr(self, "choice_serializer_class", ChoiceSerializer)
        return super().get_serializer_class()

    def filter_queryset(self, queryset):
        if self.request.query_params.get("for") != "options" or not self._model_has_is_default(queryset.model):
            return super().filter_queryset(queryset)

        original_ordering = getattr(self, "ordering", [])
        if isinstance(original_ordering, str):
            ordering = [original_ordering]
        else:
            ordering = list(original_ordering)

        self.ordering = ["-is_default", *ordering]
        try:
            return super().filter_queryset(queryset)
        finally:
            self.ordering = original_ordering

    @staticmethod
    def _model_has_is_default(model) -> bool:
        return any(field.name == "is_default" for field in model._meta.get_fields())
