from rest_framework_extensions import routers

from ..viewsets import GenreViewSet

router = routers.ExtendedDefaultRouter()
router.register(r"genres", GenreViewSet, basename="genre")

urlpatterns = router.urls