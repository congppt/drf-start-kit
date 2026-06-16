from rest_framework_extensions import routers

from ..viewsets import GroupPermissionViewSet, GroupViewSet

router = routers.ExtendedSimpleRouter()
(
    router.register(r"groups", GroupViewSet, basename="group").register(
        r"permissions", GroupPermissionViewSet, parents_query_lookups=["group"], basename="group-permissions"
    )
)

url_patterns = router.urls
