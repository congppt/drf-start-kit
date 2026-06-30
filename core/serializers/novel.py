import uuid

from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from integrations.minio import minio

from .. import models, validators
from .common import (
    ChoiceSerializer,
    ExcludeDeleteModelSerializer,
    FileAttachmentSerializer,
    FilePresignedUploadUrlSerializer,
)

COVER_FIELD_NAME = models.Novel.COVER_FIELD_NAME
COVER_IS_PUBLIC = True


class NovelSerializer(ExcludeDeleteModelSerializer):
    cover_url = serializers.SerializerMethodField()
    author = ChoiceSerializer(read_only=True)
    genres = ChoiceSerializer(many=True, read_only=True)
    status = ChoiceSerializer(read_only=True)

    class Meta:
        model = models.Novel
        exclude = []
        read_only_fields = ["slug"]

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


class NovelInputSerializer(ExcludeDeleteModelSerializer):
    slug = serializers.SlugField(read_only=True)
    genres = serializers.PrimaryKeyRelatedField(many=True, queryset=models.Genre.objects.all(), allow_empty=False)

    class Meta:
        model = models.Novel
        exclude = []
        read_only_fields = ["author"]

    def create(self, validated_data: dict):
        slug = slugify(validated_data["title"])
        if models.Novel.objects.filter(slug=slug).exists():
            slug += "-" + uuid.uuid4().hex[:8]
        validated_data["slug"] = slug
        validated_data["author"] = validated_data["performed_by"]
        try:
            return super().create(validated_data)
        except Exception as e:
            raise serializers.ValidationError("Could not create. Please try again later.") from e


class NovelCoverUploadUrlSerializer(FilePresignedUploadUrlSerializer):
    file_name = serializers.CharField(write_only=True, validators=[validators.ImageFileNameValidator()])

    is_public = COVER_IS_PUBLIC


class NovelCoverUpdateSerializer(FileAttachmentSerializer):
    is_public = COVER_IS_PUBLIC
    attachment_field_name = COVER_FIELD_NAME

    def update(self, instance: models.Novel, validated_data: dict):
        file: models.FileAsset = validated_data["file"]
        with transaction.atomic():
            instance.attachments.filter(field_name=self.attachment_field_name).delete()
            instance.attachments.create(file=file, field_name=self.attachment_field_name)
            file.status = models.UploadStatus.READY
            file.save()
        return instance
