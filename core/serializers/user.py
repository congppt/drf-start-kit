import mimetypes

from django.conf import settings
from django.contrib.auth import password_validation
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from utils.minio import minio
from .. import models
from .. import validators
from .group import GroupSerializer


AVATAR_FIELD_NAME = models.User.AVATAR_FIELD_NAME
AVATAR_IS_PUBLIC = models.User.AVATAR_IS_PUBLIC

class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    groups = GroupSerializer(many=True, read_only=True)
    class Meta:
        model = models.User
        exclude = ['password', 'user_permissions']

    def get_avatar_url(self, obj: models.User) -> str | None:
        attachment = (
            obj.attachments
            .filter(field_name=AVATAR_FIELD_NAME, file__status=models.UploadStatus.READY)
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
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=models.Group.objects.all())
    class Meta:
        model = models.User
        exclude = ['user_permissions', 'last_login', 'date_joined']

    def create(self, validated_data: dict):
        groups = validated_data.pop('groups')
        with transaction.atomic():
            user = models.User.objects.create_user(**validated_data)
            user.groups.set(groups)
        return user

class UserUpdateSerializer(UserSerializer):
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=models.Group.objects.all())
    class Meta:
        model = models.User
        exclude = ['username', 'password', 'last_login', 'date_joined', 'user_permissions']

    def update(self, instance: models.User, validated_data: dict):
        performed_by = validated_data.pop('performed_by')
        groups = validated_data.pop('groups', [])
        for key, value in validated_data.items():
            setattr(instance, key, value)
        with transaction.atomic():
            instance.save(performed_by=performed_by)
            instance.groups.set(groups)
        return instance

class UserSelfUpdateSerializer(UserSerializer):
    class Meta:
        model = models.User
        fields = ['first_name', 'last_name', 'email']

class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(validators=[password_validation.validate_password])

    def update(self, instance: models.User, validated_data: dict):
        performed_by = validated_data.pop('performed_by')
        instance.set_password(validated_data['new_password'])
        instance.save(performed_by=performed_by)
        return instance

class PasswordSelfChangeSerializer(PasswordChangeSerializer):
    old_password = serializers.CharField()
    
    def validate_old_password(self, value: str):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect')
        return value

    def validate(self, attrs: dict):
        if attrs['new_password'] == attrs['old_password']:
            raise serializers.ValidationError('New password cannot be the same as the old password')
        return attrs

class UserAvatarUploadUrlSerializer(serializers.Serializer):
    file_name = serializers.CharField(
        write_only=True,
        validators=[validators.ImageFileNameValidator()],
    )
    file_size = serializers.IntegerField(
        write_only=True,
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(settings.FILE_UPLOAD_MAX_MEMORY_SIZE)],
    )

    upload_url = serializers.CharField(read_only=True)
    file_id = serializers.UUIDField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data: dict):
        performed_by = validated_data.pop('performed_by')
        content_type, _ = mimetypes.guess_type(validated_data['file_name'])
        file_asset = models.FileAsset.objects.create(
            name=validated_data['file_name'],
            content_type=content_type,
            size=validated_data['file_size'],
            is_public=AVATAR_IS_PUBLIC,
            owner=performed_by.username,
        )
        url = minio.presigned_upload(
            file_asset.id,
            timezone.timedelta(seconds=settings.FILE_ORPHANED_INTERVAL + 60),
            is_public=AVATAR_IS_PUBLIC
        )
        return {
            'file_id': file_asset.id,
            'upload_url': url,
            'expires_at': timezone.now() + timezone.timedelta(minutes=10),
        }


class UserAvatarSelfUpdateSerializer(serializers.Serializer):
    file_id = serializers.PrimaryKeyRelatedField(queryset=models.FileAsset.objects.all())

    def validate_file_id(self, value: models.FileAsset):
        request = self.context['request']
        if value.owner != request.user.username:
            raise serializers.ValidationError('File does not belong to the current user.')
        attachment = getattr(value, 'attachment', None)
        if attachment and (
            attachment.content_object != request.user
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

    def update(self, instance: models.User, validated_data: dict):
        file_asset = validated_data['file_id']
        with transaction.atomic():
            instance.attachments.filter(field_name=AVATAR_FIELD_NAME).delete()
            instance.attachments.create(
                file=file_asset,
                field_name=AVATAR_FIELD_NAME,
            )
            file_asset.status = models.UploadStatus.READY
            file_asset.save()
        return instance