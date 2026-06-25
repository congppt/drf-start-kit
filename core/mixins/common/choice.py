from ...serializers import ChoiceSerializer


class ChoiceListModelMixin:
    def get_serializer_class(self):
        if self.request.query_params.get("for") == "options":
            return ChoiceSerializer
        return super().get_serializer_class()
