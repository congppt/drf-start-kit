from rest_framework_extensions import routers

from ..viewsets import UserViewSet

router = routers.ExtendedSimpleRouter()
router.register(r'users', UserViewSet, basename='user')
url_patterns = router.urls