from rest_framework import mixins, viewsets

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    ordering = ["-id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Personalized queryset based on the user
        return queryset