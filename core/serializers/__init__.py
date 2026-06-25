from rest_framework.serializers import ModelSerializer, Serializer

from .common import (
    AuditableModelSerializer,
    ChoiceLimitOffsetSerializer,
    ChoiceSerializer,
    ExcludeAuditableModelSerializer,
    ExcludeDeleteModelSerializer,
    LogEntrySerializer,
)
from .group import GroupChoicesSerializer, GroupSerializer
from .permission import PermissionSerializer
from .user import (
    PasswordChangeSerializer,
    PasswordSelfChangeSerializer,
    UserAvatarSelfUpdateSerializer,
    UserAvatarUploadUrlSerializer,
    UserChoicesSerializer,
    UserCreateSerializer,
    UserSelfUpdateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
