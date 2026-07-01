from rest_framework import permissions

from .. import models


class NovelPermission(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.has_perm("core.change_novel"):
            return True
        return obj.author_id == request.user.pk


class NovelChapterPermission(permissions.IsAuthenticatedOrReadOnly):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.user.has_perm("core.change_chapter"):
            return True
        if request.method not in permissions.SAFE_METHODS:
            novel_id = view.kwargs["novel_id"]
            return models.Novel.objects.filter(pk=novel_id, author=request.user).exists()
        return True
