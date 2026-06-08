from django.contrib.auth.models import User, Group
from django.contrib.auth import password_validation
from django.db import transaction
from rest_framework import serializers

from ..models import Department, UserDetail
from ..serializers.group import GroupSerializer


class UserSerializer(serializers.ModelSerializer):
    department_id = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), source='detail.department')
    groups = GroupSerializer(many=True, read_only=True)
    class Meta:
        model = User
        exclude = ['password', 'user_permissions']

class UserCreateSerializer(UserSerializer):
    password = serializers.CharField(validators=[password_validation.validate_password])
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=Group.objects.all())
    class Meta:
        model = User
        exclude = ['user_permissions', 'last_login', 'date_joined']

    def create(self, validated_data: dict):
        performed_by = validated_data.pop('performed_by')
        detail_data = validated_data.pop('detail')
        groups = validated_data.pop('groups')
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            user.groups.set(groups)
            detail = UserDetail(user=user, **detail_data)
            detail.save(performed_by=performed_by)
        return user

class UserUpdateSerializer(UserSerializer):
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=Group.objects.all())
    class Meta:
        model = User
        exclude = ['username', 'password', 'last_login', 'date_joined', 'user_permissions']

    def update(self, instance: User, validated_data: dict):
        performed_by = validated_data.pop('performed_by')
        detail_data = validated_data.pop('detail', {})
        groups = validated_data.pop('groups', [])
        instance.detail = getattr(instance, 'detail', UserDetail(**detail_data))
        for key, value in detail_data.items():
            setattr(instance.detail, key, value)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        with transaction.atomic():
            instance.save()
            instance.groups.set(groups)
            instance.detail.save(performed_by=performed_by)
        return instance

class UserSelfUpdateSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class SuperUserPasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(validators=[password_validation.validate_password])
class PasswordSelfChangeSerializer(SuperUserPasswordChangeSerializer):
    old_password = serializers.CharField()
    
    def validate(self, attrs: dict):
        if not self.context['request'].user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'Old password is incorrect'})
        return attrs

    def update(self, instance: User, validated_data: dict):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance