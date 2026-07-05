from rest_framework.serializers import ModelSerializer, Serializer

from .bookmark import UserBookmarkCreateSerializer, UserBookmarkSerializer
from .chapter import ChapterDetailSerializer, ChapterInputSerializer, ChapterListSerializer
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
from .novel import (
    NovelCoverUpdateSerializer,
    NovelCoverUploadUrlSerializer,
    NovelDetailSerializer,
    NovelInputSerializer,
    NovelListSerializer,
    NovelReadEventSerializer,
    NovelSuggestionSerializer,
)
from .permission import PermissionSerializer
from .reading_progress import (
    NovelReadingProgressInputSerializer,
    NovelReadingProgressSerializer,
    UserReadingProgressSerializer,
)
from .user import (
    PasswordChangeSerializer,
    PasswordSelfChangeSerializer,
    UserAvatarSelfUpdateSerializer,
    UserAvatarUploadUrlSerializer,
    UserChoicesSerializer,
    UserCreateSerializer,
    UserSelfSerializer,
    UserSelfUpdateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
