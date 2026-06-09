from django.conf import settings
from django.core import validators
from django.contrib.auth.models import User, Group
from django.contrib.auth import password_validation
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from utils.minio import minio
from utils.django.models.file import UploadStatus

from ..models import Department, FileAsset, UserDetail
from ..serializers.group import GroupSerializer


AVATAR_FIELD_NAME = 'avatar'
AVATAR_IS_PUBLIC = False

class UserSerializer(serializers.ModelSerializer):
    department_id = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), source='detail.department')
    avatar_url = serializers.SerializerMethodField()
    groups = GroupSerializer(many=True, read_only=True)
    class Meta:
        model = User
        exclude = ['password', 'user_permissions']

    def get_avatar_url(self, obj: User) -> str | None:
        detail = getattr(obj, 'detail', None)
        if not detail:
            return None
        attachment = (
            detail.attachments
            .filter(field_name=AVATAR_FIELD_NAME, file__status=UploadStatus.READY)
            .select_related('file')
            .first()
        )
        if not attachment:
            return None
        file_asset = attachment.file
        if file_asset.is_public:
            return minio.get_public_url(file_asset.id)
        return minio.presigned_download(file_asset.id, file_asset.name)

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

class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(validators=[password_validation.validate_password])

    def update(self, instance: User, validated_data: dict):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance

class PasswordSelfChangeSerializer(PasswordChangeSerializer):
    old_password = serializers.CharField()
    
    def validate(self, attrs: dict):
        if not self.context['request'].user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'Old password is incorrect'})
        return attrs

class UserAvatarUploadUrlSerializer(serializers.Serializer):
    file_name = serializers.CharField(write_only=True, validators=[validators.RegexValidator(regex=r'^[^/\\?%*:|"<>\x00]+$')])
    file_size = serializers.IntegerField(write_only=True, validators=[validators.MinValueValidator(1), validators.MaxValueValidator(settings.FILE_UPLOAD_MAX_MEMORY_SIZE)])
    content_type = serializers.CharField(write_only=True, validators=[validators.RegexValidator(regex=r'^image/.*$')])

    upload_url = serializers.CharField(read_only=True)
    file_id = serializers.UUIDField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data: dict):
        performed_by = validated_data.pop('performed_by')
        with transaction.atomic():
            file_asset = FileAsset.objects.create(
                name=validated_data['file_name'],
                content_type=validated_data['content_type'],
                size=validated_data['file_size'],
                is_public=AVATAR_IS_PUBLIC,
                owner=performed_by.username,
            )
            url = minio.presigned_upload(file_asset.id, timezone.timedelta(seconds=settings.FILE_ORPHANED_INTERVAL + 60), is_public=AVATAR_IS_PUBLIC)
        return {
            'file_id': file_asset.id,
            'upload_url': url,
            'expires_at': timezone.now() + timezone.timedelta(minutes=10),
        }


class UserAvatarSelfUpdateSerializer(serializers.Serializer):
    file_id = serializers.PrimaryKeyRelatedField(queryset=FileAsset.objects.all())

    def validate_file_id(self, value: FileAsset):
        request = self.context['request']
        detail = getattr(request.user, 'detail', None)
        if not detail:
            raise serializers.ValidationError('Current user does not have a detail record.')
        if value.owner != request.user.username:
            raise serializers.ValidationError('File does not belong to the current user.')
        attachment = getattr(value, 'attachment', None)
        if attachment and (
            attachment.content_object != detail
            or attachment.field_name != AVATAR_FIELD_NAME
        ):
            raise serializers.ValidationError('File is already attached to another entity.')
        file_stat = minio.stat(value.id, is_public=AVATAR_IS_PUBLIC)
        if not file_stat:
            raise serializers.ValidationError('File does not exist.')
        if file_stat.size != value.size:
            raise serializers.ValidationError('File size does not match.')
        if file_stat.content_type != value.content_type:
            raise serializers.ValidationError('File content type does not match.')
        return value

    def update(self, instance: User, validated_data: dict):
        file_asset = validated_data['file_id']
        with transaction.atomic():
            instance.detail.attachments.filter(field_name=AVATAR_FIELD_NAME).delete()
            instance.detail.attachments.create(
                file=file_asset,
                field_name=AVATAR_FIELD_NAME,
            )
            file_asset.status = UploadStatus.READY
            file_asset.save()
        return instance