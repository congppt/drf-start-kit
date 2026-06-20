import django_filters
from rest_framework import permissions, viewsets

from .. import filters, models, serializers


class LogFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name="timestamp", lookup_expr="date__gte", required=True)
    to_date = django_filters.DateFilter(field_name="timestamp", lookup_expr="date__lte", required=True)
    min_level = django_filters.ChoiceFilter(field_name="level", lookup_expr="gte", choices=models.LogLevel.choices)

    class Meta:
        model = models.LogEntry
        fields = []


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filterset_class = LogFilter
    serializer_class = serializers.LogEntrySerializer
    queryset = models.LogEntry.objects.order_by("-timestamp").all()
    search_fields = ["message"]
