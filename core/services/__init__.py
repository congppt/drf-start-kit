"""
Domain and infrastructure services.

Default DRF flow keeps entity writes in serializers. Add modules here when logic
should be reused outside the API layer or split into focused primitives that
use cases (or serializers) can compose.

Layout:
  services/<entity>.py       entity operations (user, order, ...)
  services/common/           shared helpers (file, notification, ...)

Services should not import serializers or viewsets. Use cases open transactions;
services perform focused steps inside them.
"""
