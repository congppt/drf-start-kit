from rest_framework_extensions import routers

from ..viewsets import NovelViewSet

router = routers.ExtendedDefaultRouter()
router.register(r"novels", NovelViewSet, basename="novel")
urlpatterns = router.urls
