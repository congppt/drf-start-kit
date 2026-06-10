from rest_framework import permissions


def permissions_class_factory(*perms: str):
    class RequiredPermissions(permissions.BasePermission):
        def has_permission(self, request, view):
            return request.user and request.user.has_perms(perms)
    return RequiredPermissions