from .. import models


def create_user(validated_data: dict) -> models.User:
    groups = validated_data.pop("groups")
    user = models.User.objects.create_user(**validated_data)
    user.groups.set(groups)
    return user
