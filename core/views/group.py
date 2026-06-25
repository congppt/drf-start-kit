from rest_framework_extensions import routers

from ..viewsets import GroupPermissionViewSet, GroupViewSet

router = routers.ExtendedDefaultRouter()
(
    router.register(r"groups", GroupViewSet, basename="group").register(
        r"permissions", GroupPermissionViewSet, parents_query_lookups=["group"], basename="group-permissions"
    )
)

urlpatterns = router.urls
