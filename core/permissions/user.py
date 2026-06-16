from rest_framework import permissions


class UserPermission(permissions.DjangoModelPermissions):
    """
    Extends Django model permissions for User.

    Users without ``core.view_user`` may only read their own record (retrieve/list
    scoped to self, ``permissions`` and ``permissions_self`` actions).
    """

    _SELF_READ_ACTIONS = frozenset(
        {
            "retrieve",
            "list",
            "permissions",
            "permissions_self",
        }
    )

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.has_perm("core.view_user"):
            return super().has_permission(request, view)

        if view.action in self._SELF_READ_ACTIONS:
            return True

        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.user.has_perm("core.view_user"):
            return super().has_object_permission(request, view, obj)

        if view.action in ("retrieve", "permissions"):
            return obj.pk == request.user.pk

        return super().has_object_permission(request, view, obj)
