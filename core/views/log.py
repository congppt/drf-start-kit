from rest_framework_extensions import routers

from ..viewsets import LogViewSet

router = routers.ExtendedSimpleRouter()
router.register(r"logs", LogViewSet, basename="log")

url_patterns = router.urls
