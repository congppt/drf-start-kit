from django.contrib.auth.models import Group, Permission
from django.db import transaction
from rest_framework import serializers

class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(many=True, queryset=Permission.objects.all(), write_only=True)
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']