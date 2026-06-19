from django.forms import fields
from django_filters import Filter
from django_filters.fields import ChoiceField


class TypedChoiceField(ChoiceField, fields.TypedChoiceField):
    pass


class TypedChoiceFilter(Filter):
    field_class = TypedChoiceField
