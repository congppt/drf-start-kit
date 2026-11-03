from rest_framework_extensions import routers

from .viewsets import NotificationViewSet

router = routers.ExtendedDefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = router.urls