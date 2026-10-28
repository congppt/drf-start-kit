from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle


def scoped_rate_throttle(rate_limit: str, scope_: str):
    class CustomUserRateThrottle(UserRateThrottle):
        rate = rate_limit
        scope = scope_

    return CustomUserRateThrottle
