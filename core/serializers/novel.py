from django.db import transaction
from rest_framework import serializers

from integrations.minio import minio

from .. import models, validators
from .common import FileAttachmentSerializer, FilePresignedUploadUrlSerializer

COVER_FIELD_NAME = models.Novel.COVER_FIELD_NAME
COVER_IS_PUBLIC = True


class NovelSerializer(serializers.ModelSerializer):
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = models.Novel
        fields = "__all__"
        read_only_fields = ["author", "slug"]

    def get_cover_url(self, obj: models.Novel) -> str | None:
        attachment: models.FileAttachment = (
            obj.attachments.filter(field_name=COVER_FIELD_NAME, file__status=models.UploadStatus.READY)
            .select_related("file")
            .first()
        )
        if not attachment:
            return None
        file_asset: models.FileAsset = attachment.file
        if file_asset.is_public:
            return minio.get_public_url(file_asset.id)
        return minio.presigned_download(file_asset.id, file_asset.name)


class NovelCoverUploadUrlSerializer(FilePresignedUploadUrlSerializer):
    file_name = serializers.CharField(validators=[validators.ImageFileNameValidator()])

    is_public = COVER_IS_PUBLIC


class NovelCoverUpdateSerializer(FileAttachmentSerializer):
    is_public = COVER_IS_PUBLIC
    field_name = COVER_FIELD_NAME

    def update(self, instance: models.Novel, validated_data: dict):
        file: models.FileAsset = validated_data["file"]
        with transaction.atomic():
            instance.attachments.filter(field_name=self.field_name).delete()
            instance.attachments.create(file=file, field_name=self.field_name)
            file.status = models.UploadStatus.READY
            file.save()
        return instance
