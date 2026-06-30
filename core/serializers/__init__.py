from rest_framework.serializers import ModelSerializer, Serializer

from .common import (
    AuditableModelSerializer,
    ChoiceLimitOffsetSerializer,
    ChoiceSerializer,
    ExcludeAuditableModelSerializer,
    ExcludeDeleteModelSerializer,
    LogEntrySerializer,
)
from .genre import GenreSerializer
from .group import GroupSerializer
from .novel import NovelCoverUpdateSerializer, NovelCoverUploadUrlSerializer, NovelInputSerializer, NovelSerializer
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
