"""
System actor for auditable writes without a real request user.

``SYSTEM_ACTOR`` is an unsaved ``User`` instance (``username='system'``). It is
not stored in the database. ``AuditableModel`` only needs ``performed_by.username``
to stamp ``created_by``, ``updated_by``, and ``deleted_by``.

Use ``SYSTEM_ACTOR`` when there is no authenticated caller:

- management commands and data migrations
- fixtures and bootstrap scripts
- background tasks (Huey)
- ``create_superuser`` (wired in ``core.models.user``)

Example::

    from core.constants import SYSTEM_ACTOR

    Model.objects.create(..., performed_by=SYSTEM_ACTOR)
    instance.save(performed_by=SYSTEM_ACTOR)
    instance.delete(performed_by=SYSTEM_ACTOR)
    queryset.update(..., performed_by=SYSTEM_ACTOR)

Do **not** use ``SYSTEM_ACTOR`` for Django auth flows that expect a persisted user
(``login()``, ``request.user`` permission checks, or passing it as a FK target).

For HTTP API writes, always pass ``request.user`` via viewset mixins or
``serializer.save(performed_by=request.user)``.
"""

from .models import User

SYSTEM_ACTOR = User(
    username="system",
)
