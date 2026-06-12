from django.core.validators import validate_integer, int_list_validator


class IntegerValidator:
    def __call__(self, value):
        validate_integer(value)

class IntegerListValidator:
    def __call__(self, value):
        int_list_validator(value)