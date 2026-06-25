from rest_framework_extensions import routers

from ..viewsets import MetaViewSet

router = routers.ExtendedDefaultRouter()
router.register(r"meta", MetaViewSet, basename="meta")

urlpatterns = router.urls
