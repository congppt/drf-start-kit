from rest_framework_extensions import routers

from ..viewsets import UserViewSet

router = routers.ExtendedDefaultRouter()
router.register(r"users", UserViewSet, basename="user")
urlpatterns = router.urls
