import django_filters
import env
from django import forms
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .. import mixins, models, serializers, services, filters

PAGINATION_QUERY_PARAMS = frozenset({"limit", "offset"})


class LogFilterForm(forms.Form):
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get("from_date")
        to_date = cleaned_data.get("to_date")
        if from_date and to_date:
            if from_date > to_date:
                self.add_error("to_date", "must be on or after from_date.")
            elif (to_date - from_date).days + 1 > env.LOG_RETENTION:
                raise forms.ValidationError(f"Date range cannot exceed {env.LOG_RETENTION} days.")
        return cleaned_data


class LogFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(required=True)
    to_date = django_filters.DateFilter(required=True)
    stream = django_filters.ChoiceFilter(
        choices=[(stream, stream) for stream in services.log.LOG_STREAMS], null_value=services.log.DEFAULT_STREAM
    )
    min_level = filters.TypedChoiceFilter(choices=models.LogLevel.choices, coerce=int)
    search = django_filters.CharFilter()

    class Meta:
        model = models.User
        form = LogFilterForm
        fields = []


class LogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filterset_class = LogFilter
    serializer_class = serializers.LogSerializer
    queryset = models.User.objects.none()

    def _extract_extra_filters(self, request) -> dict[str, str]:
        reserved = set(self.filterset_class.base_filters) | PAGINATION_QUERY_PARAMS
        return {key: value for key, value in request.query_params.items() if key not in reserved}

    def _get_query_params(self, request) -> dict:
        filterset = self.filterset_class(request.GET, queryset=self.queryset)
        if not filterset.is_valid():
            raise ValidationError(filterset.errors)

        data = filterset.form.cleaned_data
        return {
            "from_date": data["from_date"],
            "to_date": data["to_date"],
            "stream": data.get("stream") or services.log.DEFAULT_STREAM,
            "min_level": data.get("min_level"),
            "search": data.get("search") or None,
        }

    def filter_queryset(self, queryset):
        logs = services.log.query_logs(
            **self._get_query_params(self.request), extra_filters=self._extract_extra_filters(self.request)
        )
        return logs

    @action(detail=False, methods=["get"])
    def files(self, request):
        return Response(services.log.list_log_files())
