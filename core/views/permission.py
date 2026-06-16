from rest_framework_extensions import routers

from ..viewsets import PermissionViewSet

router = routers.ExtendedSimpleRouter()
router.register(r"permissions", PermissionViewSet, basename="permission")
url_patterns = router.urls
