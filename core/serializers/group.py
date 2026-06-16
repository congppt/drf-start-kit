from rest_framework import serializers

from .. import models


class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=models.Permission.objects.all(), write_only=True
    )

    class Meta:
        model = models.Group
        fields = ["id", "name", "permissions"]
