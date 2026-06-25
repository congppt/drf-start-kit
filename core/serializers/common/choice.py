from enum import Enum
from uuid import UUID

from django.db.models import QuerySet
from rest_framework import serializers


class ChoiceSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()
    color = serializers.CharField(default=None)

    def get_value(self, obj) -> int | str | UUID:
        if isinstance(obj, Enum):
            return obj.value
        return obj.pk

    def get_label(self, obj) -> str:
        label = getattr(obj, "label", None)
        if label is not None:
            return label
        return str(obj)


class ChoiceLimitOffsetSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(required=False)
    previous = serializers.URLField(required=False)
    results = ChoiceSerializer(many=True)
