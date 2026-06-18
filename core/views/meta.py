from rest_framework_extensions import routers

from ..viewsets import MetaViewSet

router = routers.ExtendedSimpleRouter()
router.register(r"meta", MetaViewSet, basename="meta")

url_patterns = router.urls
