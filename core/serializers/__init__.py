from rest_framework.serializers import Serializer, ModelSerializer

from .common import AuditableModelSerializer, ExcludeDeleteFieldsSerializer, ExcludeAuditFieldsSerializer
from .group import GroupSerializer
from .permission import PermissionSerializer
from .user import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserSelfUpdateSerializer,
    UserAvatarUploadUrlSerializer,
    UserAvatarSelfUpdateSerializer,
    PasswordChangeSerializer,
    PasswordSelfChangeSerializer,
)

__all__ = [
    # DRF Built-in Serializers
    Serializer,
    ModelSerializer,
    # Auditable Model Based Serializers
    AuditableModelSerializer,
    ExcludeDeleteFieldsSerializer,
    ExcludeAuditFieldsSerializer,
    #
    GroupSerializer,
    # 
    PermissionSerializer,
    #
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserSelfUpdateSerializer,
    UserAvatarUploadUrlSerializer,
    UserAvatarSelfUpdateSerializer,
    PasswordChangeSerializer,
    PasswordSelfChangeSerializer,
    #
]