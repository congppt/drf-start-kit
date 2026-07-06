from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .. import services, usecases


class WalletCreditInputSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated_data):
        try:
            return usecases.wallet.admin_credit(
                recipient=validated_data["recipient"],
                sender=self.context["request"].user,
                amount=validated_data["amount"],
                note=validated_data.get("note") or None,
            )
        except services.wallet.WalletNotFoundError:
            raise serializers.ValidationError(_("Wallet not found."))
