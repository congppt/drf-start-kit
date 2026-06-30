from django.utils import timezone
from rest_framework import serializers

from utils import lexorank

from .. import models
from .common import ExcludeDeleteModelSerializer


class ChapterListSerializer(ExcludeDeleteModelSerializer):
    class Meta:
        model = models.Chapter
        exclude = ["content"]


class ChapterDetailSerializer(ExcludeDeleteModelSerializer):
    class Meta:
        model = models.Chapter
        exclude = ["lexorank"]


class ChapterInputSerializer(ExcludeDeleteModelSerializer):
    previous = serializers.PrimaryKeyRelatedField(
        queryset=models.Chapter.objects.all(), allow_null=True, write_only=True
    )

    class Meta:
        model = models.Chapter
        exclude = ["lexorank"]
        read_only_fields = ["published_at", "novel"]

    def validate_previous(self, value):
        if not value:
            return None
        if value.novel_id != self.context["novel_id"]:
            raise serializers.ValidationError("Invalid chapter position.")
        if self.instance and value.pk == self.instance.pk:
            raise serializers.ValidationError("Invalid chapter position.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance and "previous" not in self.initial_data:
            return attrs

        novel_id = self.context["novel_id"]
        previous: models.Chapter | None = attrs.pop("previous", None)
        base_qs = models.Chapter.objects.filter(novel_id=novel_id)
        if self.instance:
            base_qs = base_qs.exclude(pk=self.instance.pk)
        if not previous:
            prev_rank = None
            next_rank = base_qs.order_by("lexorank").values_list("lexorank", flat=True).first()
        else:
            prev_rank = previous.lexorank
            next_rank = (
                base_qs.filter(lexorank__gt=prev_rank).order_by("lexorank").values_list("lexorank", flat=True).first()
            )
        try:
            attrs["lexorank"] = lexorank.get_rank(prev_rank, next_rank)
        except ValueError:
            raise serializers.ValidationError("Invalid chapter position.")
        return attrs

    def create(self, validated_data):
        is_published = validated_data.get("is_published")
        if is_published:
            validated_data["published_at"] = timezone.now()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        is_published = validated_data.get("is_published")
        if is_published and not instance.published_at:
            validated_data["published_at"] = timezone.now()
        return super().update(instance, validated_data)
