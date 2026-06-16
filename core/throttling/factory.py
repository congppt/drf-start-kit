from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


def anon_rate_throttle(rate_limit: str):
    class CustomAnonRateThrottle(AnonRateThrottle):
        rate = rate_limit

    return CustomAnonRateThrottle


def user_rate_throttle(rate_limit: str):
    class CustomUserRateThrottle(UserRateThrottle):
        rate = rate_limit

    return CustomUserRateThrottle
