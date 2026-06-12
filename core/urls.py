from django.urls import path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

urlpatterns = [
    # Swagger API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Redirect to Swagger API Documentation
    path('', RedirectView.as_view(url='schema/swagger/', permanent=True)),
    # Views URLs
    *views.url_patterns,
]