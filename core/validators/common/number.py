from django.core.validators import validate_integer, int_list_validator
from django.utils.deconstruct import deconstructible


@deconstructible
class IntegerValidator:
    def __call__(self, value):
        validate_integer(value)

    def __eq__(self, other):
        return isinstance(other, IntegerValidator)


@deconstructible
class IntegerListValidator:
    def __call__(self, value):
        int_list_validator(value)

    def __eq__(self, other):
        return isinstance(other, IntegerListValidator)
