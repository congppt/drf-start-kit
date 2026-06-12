from django.core.validators import validate_ipv4_address, validate_ipv6_address, validate_ipv46_address

class IPv4Validator:
    def __call__(self, value):
        validate_ipv4_address(value)

class IPv6Validator:
    def __call__(self, value):
        validate_ipv6_address(value)

class IPv4OrIPv6Validator:
    def __call__(self, value):
        validate_ipv46_address(value)
