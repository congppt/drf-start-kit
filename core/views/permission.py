from rest_framework_extensions import routers

from ..viewsets import PermissionViewSet

router = routers.ExtendedDefaultRouter()
router.register(r"permissions", PermissionViewSet, basename="permission")
urlpatterns = router.urls
