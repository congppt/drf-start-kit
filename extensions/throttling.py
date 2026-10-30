from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle

__CACHE = {}

def scoped_rate_throttle(rate_limit: str, scope_: str):
    class_name = f"ScopedRateThrottle{hash(rate_limit + scope_)}"
    if class_name in __CACHE:
        return __CACHE[class_name]

    class CustomUserRateThrottle(UserRateThrottle):
        rate = rate_limit
        scope = scope_

    __CACHE[class_name] = CustomUserRateThrottle
    return CustomUserRateThrottle
