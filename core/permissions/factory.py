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


def object_permission_class(field_name: str):
    class_name = f"ObjectPermission{hash(field_name)}"
    if class_name in __CACHE:
        return __CACHE[class_name]

    class RequiredObjectPermission(permissions.BasePermission):
        def has_object_permission(self, request, view, obj):
            if request.method in permissions.SAFE_METHODS:
                return True
            layers = field_name.split(".")
            field_val = obj
            for layer in layers:
                field_val = getattr(field_val, layer, None)
            if not field_val:
                return False
            return request.user.pk == field_val or request.user == field_val

    __CACHE[class_name] = RequiredObjectPermission
    return RequiredObjectPermission
