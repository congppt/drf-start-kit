from rest_framework_extensions import routers

from ..viewsets import LogViewSet

router = routers.ExtendedDefaultRouter()
router.register(r"logs", LogViewSet, basename="log")

urlpatterns = router.urls
