from urllib.parse import urlencode

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    relative_url = serializers.SerializerMethodField()

    def get_relative_url(self, obj):
        if not obj.path:
            return None
        query_strings = urlencode(obj.args)
        return f"{obj.path}?{query_strings}"

    class Meta:
        model = Notification
        exclude = ["recipient", "path", "args"]