from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from utils import lexorank

from .. import models
from .common import ExcludeDeleteModelSerializer


class ChapterListSerializer(ExcludeDeleteModelSerializer):
    is_unlocked = serializers.BooleanField(read_only=True)

    class Meta:
        model = models.Chapter
        exclude = ["content", "lexorank"]


class ChapterDetailSerializer(ExcludeDeleteModelSerializer):
    previous = serializers.SerializerMethodField()
    next = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = models.Chapter
        exclude = ["lexorank"]

    def _neighbor_qs(self, obj):
        base_qs = self.context["visible_chapters_qs"]
        return base_qs.exclude(pk=obj.pk)

    def get_previous(self, obj) -> int | None:
        pk = (
            self._neighbor_qs(obj)
            .filter(lexorank__lt=obj.lexorank)
            .order_by("-lexorank")
            .values_list("pk", flat=True)
            .first()
        )
        return pk

    def get_next(self, obj) -> int | None:
        pk = (
            self._neighbor_qs(obj)
            .filter(lexorank__gt=obj.lexorank)
            .order_by("lexorank")
            .values_list("pk", flat=True)
            .first()
        )
        return pk

    def get_content(self, obj) -> str:
        if getattr(obj, "is_unlocked", False):
            return obj.content
        return None


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
            raise serializers.ValidationError(_("Invalid chapter position."))
        if self.instance and value.pk == self.instance.pk:
            raise serializers.ValidationError(_("Invalid chapter position."))
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
            raise serializers.ValidationError(_("Invalid chapter position."))
        return attrs

    def create(self, validated_data):
        is_published = validated_data.get("is_published")
        with transaction.atomic():
            if is_published:
                validated_data["published_at"] = timezone.now()
                models.Novel.objects.filter(id=validated_data["novel_id"]).update(
                    last_publication_at=validated_data["published_at"]
                )
            return super().create(validated_data)

    def update(self, instance, validated_data):
        is_published = validated_data.get("is_published")
        with transaction.atomic():
            if is_published and not instance.is_published:
                validated_data["published_at"] = timezone.now()
                models.Novel.objects.filter(id=instance.novel_id).update(
                    last_publication_at=validated_data["published_at"]
                )
            return super().update(instance, validated_data)
