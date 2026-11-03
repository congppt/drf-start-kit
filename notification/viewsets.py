from extensions import filters, mixins, permissions
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Notification
from .serializers import NotificationSerializer


class NotificationFilter(filters.FilterSet):
    class Meta:
        model = Notification
        fields = ["category", "is_read"]

class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    ordering = ["-id"]
    search_fields = ["message"]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(recipient=self.request.user)
        return queryset

    @action(detail=True, methods=["post"], url_path="mark-as-read")
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        services.mark_as_read(notification)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], url_path="mark-all-as-read")
    def mark_all_as_read(self, request):
        services.mark_all_as_read(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)