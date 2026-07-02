import django_filters.rest_framework as filters
from djangorestframework_camel_case.util import underscoreize


class DjangoFilterBackend(filters.DjangoFilterBackend):
    def get_filterset_kwargs(self, request, queryset, view):
        return {
            "data": underscoreize(request.query_params),
            "queryset": queryset,
            "request": request,
        }
