from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from ..throttling import factory

class ThrottleTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [factory.anon_rate_throttle('5/minute')]

url_patterns = [
    path('token/', ThrottleTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]