from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_extensions import routers
from .views.auth import url_patterns as auth_urls
from .views import department, user, group, permission


router = routers.ExtendedSimpleRouter()
router.register(r'departments', department.DepartmentViewSet)
router.register(r'users', user.UserViewSet)
(
    router
    .register(r'groups', group.GroupViewSet)
    .register(
        r'permissions',
        permission.GroupPermissionViewSet,
        parents_query_lookups=['group'],
        basename='group-permissions'
    )
)
router.register(r'permissions', permission.PermissionViewSet, basename='permission')
urlpatterns = [
    path("auth/", include(auth_urls)),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('', include(router.urls)),
]