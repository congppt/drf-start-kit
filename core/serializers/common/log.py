from rest_framework import serializers

from ... import models


class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LogEntry
        exclude = []

    def create(self, validated_data) -> models.LogEntry:
        return models.LogEntry(**validated_data)
