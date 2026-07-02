from rest_framework import serializers

from .. import models
from .common import ChoiceSerializer
from .novel import NovelChoiceSerializer


class NovelReadingProgressSerializer(serializers.ModelSerializer):
    chapter = ChoiceSerializer(read_only=True)

    class Meta:
        model = models.ReadingProgress
        exclude = ["id", "user", "novel"]


class UserReadingProgressSerializer(NovelReadingProgressSerializer):
    novel = NovelChoiceSerializer(read_only=True)

    class Meta:
        model = models.ReadingProgress
        exclude = ["id", "user"]


class NovelReadingProgressInputSerializer(serializers.ModelSerializer):
    chapter = serializers.PrimaryKeyRelatedField(queryset=models.Chapter.objects.select_related("novel").all())

    class Meta:
        model = models.ReadingProgress
        fields = ["chapter"]

    def validate_chapter(self, value: models.Chapter):
        if value.novel_id != self.context["novel_id"]:
            raise serializers.ValidationError("Chapter does not belong to the novel.")
        if not value.is_published or value.novel.status == models.NovelStatus.DRAFT:
            raise serializers.ValidationError("Chapter not available.")
        return value

    def create(self, validated_data):
        instance, _ = models.ReadingProgress.objects.update_or_create(
            user=validated_data["user"],
            novel_id=validated_data["novel_id"],
            defaults={"chapter": validated_data["chapter"]},
        )
        return instance

    def update(self, instance, validated_data):
        instance.chapter = validated_data["chapter"]
        instance.save(performed_by=self.context["user"])
        return instance
