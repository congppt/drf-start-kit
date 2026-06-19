from rest_framework import serializers

from .. import models


class LogSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(source="time.repr")
    level = serializers.ChoiceField(choices=models.LogLevel.choices, source="level.name")
    message = serializers.CharField(allow_blank=True)
    extra = serializers.DictField()
