from django.urls import path
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from .. import serializers, throttling


class ThrottleTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [throttling.AuthThrottle, throttling.factory.per_view_anon_rate_throttle("30/minute")]


class ThrottleTokenRefreshView(TokenRefreshView):
    throttle_classes = [throttling.ReAuthThrottle, throttling.factory.per_view_anon_rate_throttle("30/minute")]


class PasswordResetRequestView(APIView):
    throttle_classes = [throttling.factory.per_view_anon_rate_throttle("5/minute")]
    serializer_class = serializers.PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # 204 when the email matches an active account.
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetConfirmView(APIView):
    throttle_classes = [throttling.factory.per_view_anon_rate_throttle("5/minute")]
    serializer_class = serializers.PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


urlpatterns = [
    path("token/", ThrottleTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", ThrottleTokenRefreshView.as_view(), name="token_refresh"),
    path("token/logout/", TokenBlacklistView.as_view(), name="token_logout"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]
