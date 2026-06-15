from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from ..throttling import factory


class ThrottleTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [factory.anon_rate_throttle("5/minute")]


class ThrottleTokenRefreshView(TokenRefreshView):
    throttle_classes = [factory.anon_rate_throttle("5/minute")]


url_patterns = [
    path("token/", ThrottleTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", ThrottleTokenRefreshView.as_view(), name="token_refresh"),
    path("token/logout/", TokenBlacklistView.as_view(), name="token_logout"),
]
