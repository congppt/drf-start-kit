from rest_framework.serializers import ModelSerializer, Serializer

from .common import AuditableModelSerializer, ExcludeAuditableModelSerializer, ExcludeDeleteModelSerializer
from .group import GroupSerializer
from .permission import PermissionSerializer
from .user import (
    PasswordChangeSerializer,
    PasswordSelfChangeSerializer,
    UserAvatarSelfUpdateSerializer,
    UserAvatarUploadUrlSerializer,
    UserCreateSerializer,
    UserSelfUpdateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)