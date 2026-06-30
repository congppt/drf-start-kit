from rest_framework import permissions

__CACHE = {}


def permissions_class(*perms: str):
    class_name = f"RequiredPermissions{hash(perms)}"
    if class_name in __CACHE:
        return __CACHE[class_name]

    class RequiredPermissions(permissions.BasePermission):
        def has_permission(self, request, view):
            return request.user and request.user.has_perms(perms)

    __CACHE[class_name] = RequiredPermissions
    return RequiredPermissions
