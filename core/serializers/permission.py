from rest_framework import serializers

from .. import models


class PermissionSerializer(serializers.ModelSerializer):
    model = serializers.CharField(source="content_type.model", read_only=True)

    class Meta:
        model = models.Permission
        fields = ["id", "name", "model"]
