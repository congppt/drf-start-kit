import mimetypes

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from integrations.minio import minio

from ... import models, validators


class FilePresignedUploadUrlSerializer(serializers.Serializer):
    """
    Request a presigned upload URL and create a pending ``FileAsset``.

    Subclass or pass ``is_public`` and ``file_name_validator`` for endpoint-specific rules.
    """

    file_name = serializers.CharField(write_only=True)
    file_size = serializers.IntegerField(
        write_only=True,
        validators=[validators.FileSizeValidator()],
    )

    upload_url = serializers.CharField(read_only=True)
    file_id = serializers.UUIDField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)

    is_public = False
    upload_ttl_seconds = settings.FILE_ORPHANED_INTERVAL

    def create(self, validated_data: dict):
        performed_by = validated_data.pop("performed_by")
        content_type, _ = mimetypes.guess_type(validated_data["file_name"])
        if not content_type:
            # MinIO default content type
            content_type = "application/octet-stream"
        file_asset = models.FileAsset.objects.create(
            name=validated_data["file_name"],
            content_type=content_type,
            size=validated_data["file_size"],
            is_public=self.is_public,
            owner=performed_by.username,
        )
        url = minio.presigned_upload(
            file_asset.id,
            timezone.timedelta(seconds=self.upload_ttl_seconds + 60),
            is_public=self.is_public,
        )
        return {
            "file_id": file_asset.id,
            "upload_url": url,
            "expires_at": timezone.now() + timezone.timedelta(seconds=self.upload_ttl_seconds),
        }


class FileAttachmentSerializer(serializers.Serializer):
    """
    Attach a previously uploaded ``FileAsset`` to a model instance.

    Validates ownership, MinIO object presence, and optional field binding.
    """

    file = serializers.PrimaryKeyRelatedField(queryset=models.FileAsset.objects.all())

    field_name = "attachment"
    is_public = False

    def validate_file(self, value: models.FileAsset):
        request = self.context["request"]
        if value.owner != request.user.username:
            raise serializers.ValidationError(_("Please choose a file that you uploaded."))

        attachment = value.attachments.select_related("content_type").first()
        if (
            attachment
            and self.field_name
            and (attachment.content_object != self.instance or attachment.field_name != self.field_name)
        ):
            raise serializers.ValidationError(_("This file is already attached to another record."))

        file_stat = minio.stat(value.id, is_public=self.is_public)
        if not file_stat:
            raise serializers.ValidationError(_("We could not find the uploaded file."))
        if file_stat.size != value.size:
            raise serializers.ValidationError(_("The uploaded file is invalid. Please upload it again."))
        if file_stat.content_type != value.content_type:
            raise serializers.ValidationError(_("This file type is not supported. Please upload another file."))
        return value
