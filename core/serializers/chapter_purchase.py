from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .. import models, services, usecases


class ChapterPurchaseInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ChapterPurchase
        fields = ["chapter"]
        extra_kwargs = {
            "chapter": {"write_only": True},
        }

    def validate(self, attrs):
        chapter = attrs["chapter"]
        user = self.context["request"].user

        if models.ChapterPurchase.objects.filter(user=user, chapter=chapter).exists():
            return attrs

        if not chapter.is_published or chapter.novel.status == models.NovelStatus.DRAFT:
            raise serializers.ValidationError({"chapter": _("Chapter is not available for purchase.")})
        if chapter.price == 0:
            raise serializers.ValidationError({"chapter": _("Chapter is free.")})
        if chapter.novel.author_id == user.pk:
            raise serializers.ValidationError({"chapter": _("Authors cannot purchase their own chapters.")})

        try:
            wallet = models.Wallet.objects.get(user=user)
        except models.Wallet.DoesNotExist:
            raise serializers.ValidationError(_("Wallet not found."))
        if wallet.balance < chapter.price:
            raise serializers.ValidationError(_("Insufficient balance."))

        return attrs

    def create(self, validated_data):
        try:
            return usecases.chapter.purchase(
                user=self.context["request"].user,
                chapter=validated_data["chapter"],
            ).created
        except services.wallet.InsufficientBalanceError:
            raise serializers.ValidationError(_("Insufficient balance."))
        except services.wallet.WalletNotFoundError:
            raise serializers.ValidationError(_("Wallet not found."))
