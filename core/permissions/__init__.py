from rest_framework.permissions import (
    AllowAny,
    DjangoModelPermissions,
    IsAdminUser,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)

from . import factory
