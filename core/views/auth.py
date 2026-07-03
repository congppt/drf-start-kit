from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from .. import throttling


class ThrottleTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [throttling.AuthThrottle, throttling.factory.per_view_anon_rate_throttle("30/minute")]


class ThrottleTokenRefreshView(TokenRefreshView):
    throttle_classes = [throttling.ReAuthThrottle, throttling.factory.per_view_anon_rate_throttle("30/minute")]


urlpatterns = [
    path("token/", ThrottleTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", ThrottleTokenRefreshView.as_view(), name="token_refresh"),
    path("token/logout/", TokenBlacklistView.as_view(), name="token_logout"),
]
