from extensions import filters, permissions
from rest_framework import viewsets

from . import models, serializers


class LogFilter(filters.FilterSet):
    from_date = filters.DateFilter(field_name="timestamp", lookup_expr="date__gte", required=True)
    to_date = filters.DateFilter(field_name="timestamp", lookup_expr="date__lte", required=True)
    min_level = filters.ChoiceFilter(field_name="level", lookup_expr="gte", choices=models.LogLevel.choices)

    class Meta:
        model = models.LogEntry
        fields = []


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    filterset_class = LogFilter
    serializer_class = serializers.LogEntrySerializer
    queryset = models.LogEntry.objects.order_by("-timestamp").all()
    search_fields = ["message"]
