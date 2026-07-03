import uuid

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


def per_view_anon_rate_throttle(rate_limit: str):
    scope_param = uuid.uuid4().hex

    class CustomAnonRateThrottle(AnonRateThrottle):
        rate = rate_limit
        scope = scope_param

    return CustomAnonRateThrottle


def per_view_user_rate_throttle(rate_limit: str):
    scope_param = uuid.uuid4().hex

    class CustomUserRateThrottle(UserRateThrottle):
        rate = rate_limit
        scope = scope_param

    return CustomUserRateThrottle
