from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly

from . import factory

__all__ = [
    # DRF Built-in Permissions
    DjangoModelPermissions,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly,
    # Custom Permissions Classes Factory
    factory
]