from django.db import transaction

from .. import models, services


def create(validated_data: dict) -> models.User:
    with transaction.atomic():
        return services.user.create_user(validated_data)
