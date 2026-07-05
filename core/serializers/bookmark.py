from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .. import models
from . import novel


class UserBookmarkSerializer(serializers.ModelSerializer):
    novel = novel.NovelListSerializer()

    class Meta:
        model = models.Bookmark
        fields = ["id", "novel", "created_at"]


class UserBookmarkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bookmark
        exclude = ["user"]
        read_only_fields = ["created_at"]
        validators = []

    def validate_novel(self, value: models.Novel):
        if value.status == models.NovelStatus.DRAFT:
            raise serializers.ValidationError(_("Novel is not published."))
        return value

    def validate(self, attrs: dict):
        attrs = super().validate(attrs)
        if models.Bookmark.objects.filter(
            user=self.context["request"].user,
            novel=attrs["novel"],
        ).exists():
            raise serializers.ValidationError(_("Bookmark already exists."))
        return attrs
