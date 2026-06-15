from django.core.validators import validate_ipv4_address, validate_ipv6_address, validate_ipv46_address
from django.utils.deconstruct import deconstructible


@deconstructible
class IPv4Validator:
    def __call__(self, value):
        validate_ipv4_address(value)

    def __eq__(self, other):
        return isinstance(other, IPv4Validator)


@deconstructible
class IPv6Validator:
    def __call__(self, value):
        validate_ipv6_address(value)

    def __eq__(self, other):
        return isinstance(other, IPv6Validator)


@deconstructible
class IPv4OrIPv6Validator:
    def __call__(self, value):
        validate_ipv46_address(value)

    def __eq__(self, other):
        return isinstance(other, IPv4OrIPv6Validator)
