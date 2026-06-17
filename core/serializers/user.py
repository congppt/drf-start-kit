from django.contrib.auth import password_validation
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from integrations.minio import minio

from .. import models, validators
from .common import ExcludeDeleteModelSerializer, FileAttachSerializer, FilePresignedUploadUrlSerializer
from .group import GroupSerializer

AVATAR_FIELD_NAME = models.User.AVATAR_FIELD_NAME
AVATAR_IS_PUBLIC = models.User.AVATAR_IS_PUBLIC


class UserPreferencesSerializer(serializers.Serializer):
    theme = serializers.CharField()
    lang = serializers.CharField()


class UserSerializer(ExcludeDeleteModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    groups = GroupSerializer(many=True, read_only=True)
    preferences = UserPreferencesSerializer(required=False)

    class Meta:
        model = models.User
        exclude = ["password", "user_permissions"]

    def get_avatar_url(self, obj: models.User) -> str | None:
        attachment = (
            obj.attachments.filter(field_name=AVATAR_FIELD_NAME, file__status=models.UploadStatus.READY)
            .select_related("file")
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
        exclude = ["user_permissions", "last_login", "date_joined"]

    def create(self, validated_data: dict):
        groups = validated_data.pop("groups")
        with transaction.atomic():
            user = models.User.objects.create_user(**validated_data)
            user.groups.set(groups)
        return user


class UserUpdateSerializer(UserSerializer):
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=models.Group.objects.all())

    class Meta:
        model = models.User
        exclude = ["username", "password", "last_login", "date_joined", "user_permissions"]

    def update(self, instance: models.User, validated_data: dict):
        performed_by = validated_data.pop("performed_by")
        groups = validated_data.pop("groups", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        with transaction.atomic():
            instance.save(performed_by=performed_by)
            if groups is not None:
                instance.groups.set(groups)
        return instance


class UserSelfUpdateSerializer(UserUpdateSerializer):
    class Meta:
        model = models.User
        fields = ["first_name", "last_name", "email", "preferences"]


class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(validators=[password_validation.validate_password])

    def update(self, instance: models.User, validated_data: dict):
        performed_by = validated_data.pop("performed_by")
        instance.set_password(validated_data["new_password"])
        instance.save(performed_by=performed_by)
        return instance


class PasswordSelfChangeSerializer(PasswordChangeSerializer):
    old_password = serializers.CharField()

    def validate_old_password(self, value: str):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError(_("The current password is incorrect."))
        return value

    def validate(self, attrs: dict):
        if attrs["new_password"] == attrs["old_password"]:
            raise serializers.ValidationError(_("The new password must be different from the current password."))
        return attrs


class UserAvatarUploadUrlSerializer(FilePresignedUploadUrlSerializer):
    file_name = serializers.CharField(validators=[validators.ImageFileNameValidator()])

    is_public = AVATAR_IS_PUBLIC


class UserAvatarSelfUpdateSerializer(FileAttachSerializer):
    is_public = AVATAR_IS_PUBLIC
    field_name = AVATAR_FIELD_NAME

    def update(self, instance: models.User, validated_data: dict):
        file = validated_data["file"]
        with transaction.atomic():
            instance.attachments.filter(field_name=self.field_name).delete()
            instance.attachments.create(file=file, field_name=self.field_name)
            file.status = models.UploadStatus.READY
            file.save()
        return instance
