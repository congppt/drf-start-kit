from uuid import UUID

from django.db import models
from rest_framework import serializers


class BaseChoiceSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()
    color = serializers.CharField(default=None)

    def get_value(self, obj) -> int | str | UUID:
        if isinstance(obj, models.Model):
            return obj.pk
        return obj

    def get_label(self, obj) -> str:
        label = getattr(obj, "label", None)
        if label is not None:
            return label
        return str(obj)


class ChoiceSerializer(BaseChoiceSerializer):
    group = serializers.CharField(default=None)
    is_default = serializers.BooleanField(default=False)


class ChoiceLimitOffsetSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(required=False)
    previous = serializers.URLField(required=False)
    results = BaseChoiceSerializer(many=True)
