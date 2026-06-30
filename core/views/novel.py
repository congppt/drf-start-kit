from rest_framework_extensions import routers

from ..viewsets import NovelChapterViewSet, NovelViewSet

router = routers.ExtendedDefaultRouter()
router.register(r"novels", NovelViewSet, basename="novel").register(
    r"chapters", NovelChapterViewSet, parents_query_lookups=["novel_id"], basename="novel-chapters"
)
urlpatterns = router.urls
