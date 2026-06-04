from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import routers
from .views.auth import url_patterns as auth_urls
from .views import department, user

router = routers.DefaultRouter()
router.register(r'departments', department.DepartmentViewSet)
router.register(r'users', user.UserViewSet)

urlpatterns = [
    path("auth/", include(auth_urls)),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
urlpatterns += router.urls