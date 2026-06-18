from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models.attachment import UploadStatus


def __to_limit_offset_response(choices: list[dict]) -> dict:
    return {"count": len(choices), "next": None, "previous": None, "results": choices}


CHOICE_REGISTRY: dict[str, type[models.TextChoices]] = {
    "upload-status": __to_limit_offset_response([
        {"value": status.value, "label": status.label}
        for status in UploadStatus
    ]),
}


class MetaViewSet(viewsets.GenericViewSet):
    @action(detail=False, methods=["get"], url_path="choices")
    def all_choices(self, request):
        return Response(CHOICE_REGISTRY)

    @action(detail=False, methods=["get"], url_path=r"choices/(?P<key>[\w-]+)")
    def choice(self, request, key: str):
        choices = CHOICE_REGISTRY.get(key)
        if choices is None:
            raise exceptions.NotFound(_("Choices not found."))
        return Response(choices)
