from django.utils.text import camel_case_to_spaces, slugify
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, viewsets
from rest_framework.compat import inflection
from rest_framework.decorators import action
from rest_framework.response import Response

from .. import models, serializers


def _build_choice_registry(*choice_types: type[models.Choices]) -> dict[str, type[models.Choices]]:
    registry: dict[str, type[models.Choices]] = {}
    for type_ in choice_types:
        slug = inflection.pluralize(slugify(camel_case_to_spaces(type_.__name__)))
        if slug in registry:
            raise ValueError(f"Duplicate choice slug {slug!r} for {type_.__name__}")
        registry[slug] = type_
    return registry


def _to_limit_offset_data(choices: type[models.Choices]) -> dict:
    return {"count": len(choices), "next": None, "previous": None, "results": list(choices)}


CHOICE_REGISTRY = _build_choice_registry(models.UploadStatus, models.LogLevel)


class MetaViewSet(viewsets.GenericViewSet):
    @action(
        detail=False,
        methods=["get"],
        url_path=r"(?P<key>[\w-]+)",
        serializer_class=serializers.ChoiceLimitOffsetSerializer,
    )
    def choices(self, request, key: str):
        choices_class = CHOICE_REGISTRY.get(key)
        if choices_class is None:
            raise exceptions.NotFound(_("Choices not found."))
        data = _to_limit_offset_data(choices_class)
        serializer = self.get_serializer(data)
        return Response(serializer.data)
