from djangorestframework_camel_case.util import camel_to_underscore
from rest_framework import filters

DUNDERSCORE_CAMELIZE_RE = r"(^_[a-z0-9])|([a-z0-9]{1}_[a-z0-9])"


class OrderingFilter(filters.OrderingFilter):
    """
    An extension of the standard ordering filter that ensures the API ordering query params are all camel cased.
    """

    def get_ordering(self, request, queryset, view):
        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [camel_to_underscore(param.strip()) for param in params.split(",")]
            ordering = self.remove_invalid_fields(queryset, fields, view, request)
            if ordering:
                return ordering

        # No ordering was included, or all the ordering fields were invalid
        return self.get_default_ordering(view)
