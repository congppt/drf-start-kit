from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from djangorestframework_camel_case.settings import api_settings
from djangorestframework_camel_case.util import camelize
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .. import models
from ..constants import SYSTEM_ACTOR
from ..tasks.email import send_password_reset_email


class TokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token.payload[settings.SIMPLE_JWT["USERNAME_CLAIM"]] = user.username
        # camelize token claims with similar rules as DRF JSON renderer
        token.payload = camelize(token.payload, **api_settings.JSON_UNDERSCOREIZE)

        return token


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def validate_email(self, value: str) -> models.User:
        user = models.User.objects.filter(
            email__iexact=value,
            is_active=True,
        ).first()
        if not user or not user.has_usable_password():
            raise serializers.ValidationError(_("No active account was found with that email."))
        return user

    def create(self, validated_data: dict):
        user: models.User = validated_data["email"]
        send_password_reset_email(user.pk)
        return {}


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[password_validation.validate_password])

    def validate(self, attrs: dict):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = models.User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, models.User.DoesNotExist) as exc:
            raise serializers.ValidationError(_("The password reset link is invalid or has expired.")) from exc

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(_("The password reset link is invalid or has expired."))

        attrs["user"] = user
        return attrs

    def create(self, validated_data: dict):
        user: models.User = validated_data["user"]
        with transaction.atomic():
            user.set_password(validated_data["new_password"])
            user.save(performed_by=SYSTEM_ACTOR)
            BlacklistedToken.objects.bulk_create(
                [
                    BlacklistedToken(token_id=token_id)
                    for token_id in OutstandingToken.objects.filter(user=user).values_list("pk", flat=True)
                ],
                ignore_conflicts=True,
            )
        return {}
