from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class ChoiceSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField(required=False)

    def get_label(self, obj):
        label = getattr(obj, "label", None)
        if label is not None:
            return _(label)
        return str(obj)

    def get_color(self, obj):
        return getattr(obj, "color", None)


class ChoiceLimitOffsetSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(required=False)
    previous = serializers.URLField(required=False)
    results = ChoiceSerializer(many=True)
