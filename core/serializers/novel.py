from rest_framework import serializers

from integrations.minio import minio

from .. import models

COVER_FIELD_NAME = models.Novel.COVER_FIELD_NAME

class NovelSerializer(serializers.ModelSerializer):
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = models.Novel
        fields = '__all__'
        read_only_fields = ['author', 'slug']

    def get_cover_url(self, obj: models.Novel) -> str | None:
        attachment = (
            obj.attachments.filter(field_name=COVER_FIELD_NAME, file__status=models.UploadStatus.READY)
            .select_related("file")
            .first()
        )
        if not attachment:
            return None
        file_asset = attachment.file
        if file_asset.is_public:
            return minio.get_public_url(file_asset.id)
        return minio.presigned_download(file_asset.id, file_asset.name)