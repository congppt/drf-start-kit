from django.contrib.auth.models import Permission, ContentType
from rest_framework import serializers

class PermissionSerializer(serializers.ModelSerializer):
    model = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all(), source='content_type.model')
    class Meta:
        model = Permission
        fields = ['id', 'name', 'model']