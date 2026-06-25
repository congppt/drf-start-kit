from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

__CACHE = {}
def anon_rate_throttle(rate_limit: str):
    class_name = f"Max{rate_limit}AnonRateThrottle"
    if class_name in __CACHE:
        return __CACHE[class_name]

    class CustomAnonRateThrottle(AnonRateThrottle):
        rate = rate_limit

    CustomAnonRateThrottle.__name__ = class_name
    CustomAnonRateThrottle.__qualname__ = class_name
    __CACHE[class_name] = CustomAnonRateThrottle
    return CustomAnonRateThrottle


def user_rate_throttle(rate_limit: str):
    class_name = f"Max{rate_limit}UserRateThrottle"
    if class_name in __CACHE:
        return __CACHE[class_name]

    class CustomUserRateThrottle(UserRateThrottle):
        rate = rate_limit

    CustomUserRateThrottle.__name__ = class_name
    CustomUserRateThrottle.__qualname__ = class_name
    __CACHE[class_name] = CustomUserRateThrottle
    return CustomUserRateThrottle
