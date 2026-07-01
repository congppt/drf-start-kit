from rest_framework.permissions import DjangoModelPermissions, IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly

from . import factory
from .novel import NovelChapterPermission, NovelPermission
