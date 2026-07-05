import uuid

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
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
READ_EVENT_CREATE_RESTRICTED_SECONDS = models.NovelReadEvent.CREATE_RESTRICTED_SECONDS


class NovelListSerializer(ExcludeDeleteModelSerializer):
    cover_url = serializers.SerializerMethodField()
    author = ChoiceSerializer(read_only=True)
    genres = ChoiceSerializer(many=True, read_only=True)
    status = ChoiceSerializer(read_only=True)

    class Meta:
        model = models.Novel
        exclude = []

    def get_cover_url(self, obj: models.Novel) -> str | None:
        file_asset: models.FileAsset | None = None
        for attachment in obj.attachments.all():
            if attachment.field_name == COVER_FIELD_NAME and attachment.file.status == models.UploadStatus.READY:
                file_asset = attachment.file
                break
        if not file_asset:
            return None
        if file_asset.is_public:
            return minio.get_public_url(file_asset.id)
        return minio.presigned_download(file_asset.id, file_asset.name)


class NovelSuggestionSerializer(NovelListSerializer):
    read_count = serializers.IntegerField(read_only=True, default=0)
    weekly_read_count = serializers.IntegerField(read_only=True, default=0)


class NovelDetailSerializer(NovelSuggestionSerializer):
    has_bookmark = serializers.BooleanField(read_only=True, default=False)


class NovelChoiceSerializer(ChoiceSerializer):
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj: models.Novel) -> str | None:
        file_asset: models.FileAsset | None = None
        for attachment in obj.attachments.all():
            if attachment.field_name == COVER_FIELD_NAME and attachment.file.status == models.UploadStatus.READY:
                file_asset = attachment.file
                break
        if not file_asset:
            return None
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
            raise serializers.ValidationError(_("Could not create. Please try again later.")) from e


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


class NovelReadEventSerializer(serializers.ModelSerializer):
    viewer_id = serializers.CharField(write_only=True)

    class Meta:
        model = models.NovelReadEvent
        fields = "__all__"
        validators = []

    def validate(self, attrs: dict):
        attrs = super().validate(attrs)
        if models.NovelReadEvent.objects.filter(
            novel=attrs["novel"],
            viewer_id=attrs["viewer_id"],
            created_at__gte=timezone.now() - timezone.timedelta(seconds=READ_EVENT_CREATE_RESTRICTED_SECONDS),
        ).exists():
            raise serializers.ValidationError(_("Today's read counted"))
        return attrs
