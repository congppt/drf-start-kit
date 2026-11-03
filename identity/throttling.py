import contextlib

from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken


class AuthThrottle(SimpleRateThrottle):
    rate = "10/minute"
    scope = "auth"

    def get_cache_key(self, request, view):
        username = request.data.get("username")
        if not username:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": username.lower(),
        }


class ReAuthThrottle(SimpleRateThrottle):
    rate = "5/minute"
    scope = "reauth"

    def get_cache_key(self, request, view):
        with contextlib.suppress(Exception):
            token_raw = request.data["refresh"]
            token = RefreshToken(token_raw)
            return self.cache_format % {
                "scope": self.scope,
                "ident": str(token[settings.SIMPLE_JWT["USER_ID_CLAIM"]]).lower(),
            }
