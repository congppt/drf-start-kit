from django.contrib.auth.models import User
from rest_framework import serializers

from ..models import Department

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    department_id = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), source='detail.department_id')
    class Meta:
        model = User
        read_only_fields = ['username', 'last_login', 'date_joined']
        exclude = ['groups', 'user_permissions']

    def create(self, validated_data):
        pass