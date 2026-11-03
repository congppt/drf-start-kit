from django.urls import path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

import env

from .views import liveness, readiness

urlpatterns = [
    path("health/live/", liveness, name="health_liveness"),
    path("health/ready/", readiness, name="health_readiness"),
]

if not env.IS_PRODUCTION:
    urlpatterns.extend(
        [
            path("schema/", SpectacularAPIView.as_view(), name="schema"),
            path("schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
            path("", RedirectView.as_view(url="schema/swagger/", permanent=False)),
        ]
    )
