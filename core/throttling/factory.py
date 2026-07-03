import contextlib
import uuid

from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle


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


def per_view_signed_cookie_rate_throttle(rate_limit: str, cookie_name: str, max_age: int):
    scope_param = uuid.uuid4().hex

    class CustomCookieRateThrottle(SimpleRateThrottle):
        rate = rate_limit
        scope = scope_param

        def get_cache_key(self, request, view):
            with contextlib.suppress(Exception):
                return self.cache_format % {
                    "scope": self.scope,
                    "ident": request.get_signed_cookie(cookie_name, max_age=max_age),
                }
            return None

    return CustomCookieRateThrottle
