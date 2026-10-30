from attachment.models import FileAsset, UploadStatus
from attachment.serializers import (
    FileAttachmentUpdateSerializerMixin,
    FilePresignedUploadUrlSerializer,
)
from django.contrib.auth import password_validation
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from extensions import validators
from extensions.serializers import BaseChoiceSerializer
from rest_framework import serializers

from identity.models import Group
from identity.serializers import PermissionSerializer
from integrations.minio import minio
from shared_kernel.serializers import ExcludeDeleteModelSerializer

from .models import User

AVATAR_FIELD_NAME = User.AVATAR_FIELD_NAME
AVATAR_IS_PUBLIC = User.AVATAR_IS_PUBLIC


class UserPreferencesSerializer(serializers.Serializer):
    theme = serializers.CharField(required=False)
    lang = serializers.CharField(required=False)


class UserSerializer(ExcludeDeleteModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    groups = BaseChoiceSerializer(many=True, read_only=True)
    preferences = UserPreferencesSerializer(required=False)

    class Meta:
        model = User
        exclude = ["password", "user_permissions"]

    def get_avatar_url(self, obj: User) -> str | None:
        attachment = (
            obj.attachments.filter(field_name=AVATAR_FIELD_NAME, file__status=UploadStatus.READY)
            .select_related("file")
            .first()
        )
        if not attachment:
            return None
        file_asset = attachment.file
        if file_asset.is_public:
            return minio.get_public_url(file_asset.id)
        return minio.presigned_download(file_asset.id, file_asset.name)


class UserUpdateSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=Group.objects.all())
    preferences = UserPreferencesSerializer(required=False)

    class Meta:
        model = User
        exclude = ["username", "password", "last_login", "date_joined", "user_permissions"]

    def validate_email(self, value: str):
        if not value:
            return value
        qs = User.all_objects.filter(email__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(_("A user with that email already exists."))
        return value

    def update(self, instance: User, validated_data: dict):
        performed_by = validated_data.pop("performed_by")
        groups = validated_data.pop("groups", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        with transaction.atomic():
            instance.save(performed_by=performed_by)
            if groups is not None:
                instance.groups.set(groups)
        return instance


class UserCreateSerializer(UserUpdateSerializer):
    password = serializers.CharField(validators=[password_validation.validate_password])

    class Meta:
        model = User
        exclude = ["user_permissions", "last_login", "date_joined"]

    def create(self, validated_data: dict):
        groups = validated_data.pop("groups")
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            user.groups.set(groups)
        return user


class UserSelfUpdateSerializer(FileAttachmentUpdateSerializerMixin, UserUpdateSerializer):
    avatar = serializers.PrimaryKeyRelatedField(
        queryset=FileAsset.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "preferences", "avatar"]

    def validate_avatar(self, value: FileAsset):
        return self.get_attachment_input_serializer(
            field_name=AVATAR_FIELD_NAME,
            is_public=AVATAR_IS_PUBLIC,
        ).validate_file(value)

    def update(self, instance: User, validated_data: dict):
        avatar = validated_data.pop("avatar", None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if avatar is not None:
                self.link_attachment(
                    instance,
                    field_name=AVATAR_FIELD_NAME,
                    unique=True,
                    files=[avatar],
                )
        return instance


class UserSelfSerializer(serializers.Serializer):
    user = UserSerializer()
    permissions = PermissionSerializer(many=True)


class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(validators=[password_validation.validate_password])

    def update(self, instance: User, validated_data: dict):
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
    file_name = serializers.CharField(write_only=True, validators=[validators.ImageFileNameValidator()])

    is_public = AVATAR_IS_PUBLIC
