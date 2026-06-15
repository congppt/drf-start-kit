# DRF Start Kit

A starter kit for building APIs with Django REST Framework. It provides a ready-to-extend project layout with JWT authentication, model permissions, filtering, pagination, auditable models, reusable validators, background jobs, caching helpers, OpenAPI documentation, and MinIO object storage integration.

The default API is exposed under `/api/`. Swagger UI is available at `/api/schema/swagger/`.

## Project Structure

```text
config/                 Django project settings, ASGI/WSGI, root URLs
core/                   Main application package
  models/               Domain models and shared model base classes
  serializers/          DRF serializers grouped by resource
  viewsets/             DRF viewsets and action routing
  views/                URL registration and non-viewset endpoints
  permissions/          Permission exports and permission factories
  pagination/           Pagination classes and factories
  mixins/               DRF and auditable model mixins
  validators/           Django, DRF, and project validators
  tasks/                Huey background and periodic tasks
  migrations/           Django schema migrations
integrations/           External service clients, for example MinIO
utils/                  Shared helpers such as cache and logging
manage.py               Django management entry point
docker-compose.yml      Local services: app, worker, Postgres, Redis, MinIO
```

`core.views.__init__` automatically imports URL modules and collects their `url_patterns`, so adding a new file under `core/views/` can register endpoints without editing a central list.

## Coding Convention

- Keep each resource split by layer: model in `core/models`, serializer in `core/serializers`, viewset in `core/viewsets`, and URL registration in `core/views`.
- Prefer DRF `ViewSet`/`GenericViewSet` classes with explicit mixins for the supported actions.
- Put request validation in serializers and reusable field validation in `core/validators`.
- Prefer explicit `Meta.fields` in serializers so the API contract is easy to review. When using `Meta.exclude` or inherited serializers for auditable models, inherit from the common serializer bases in `core.serializers.common` instead of repeating audit or soft-delete `exclude` and `read_only_fields` definitions.
- Use `get_serializer_class()` when different actions need different read/write serializers.
- Pass `performed_by=request.user` when creating, updating, or deleting auditable models.
- Use `select_related()` and `prefetch_related()` on viewset querysets when serializers access related objects.
- APIs use camelCase JSON through `djangorestframework-camel-case`; Python code stays snake_case.
- Group imports in this order: standard library, third-party packages, then local project imports. Prefer package-level relative imports inside `core`, for example `from .. import models`, `serializers`, `permissions`, `pagination`, and `mixins`.
- Name environment variables in uppercase snake case. Use double underscores to namespace service-specific settings, for example `MINIO__ENDPOINT`, `MINIO__ACCESS_KEY`, `MINIO__PUBLIC_BUCKET`; keep shared settings simple, for example `ENV`, `DB_URL`, `REDIS_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`.

## Auditable Models

`core.models.common.AuditableModel` adds audit fields and soft delete behavior:

- `created`, `created_by`
- `updated`, `updated_by`
- `is_deleted`, `deleted`, `deleted_by`

The default `objects` manager hides soft-deleted rows. Use `all_objects` when an admin or maintenance flow must include deleted records.

Auditable writes require an actor:

```python
serializer.save(performed_by=request.user)
instance.delete(performed_by=request.user)
Model.objects.create(..., performed_by=request.user)
Model.objects.filter(...).update(..., performed_by=request.user)
```

`CreateAuditableModelMixin`, `UpdateAuditableModelMixin`, `DestroyAuditableModelMixin`, and `AuditableModelViewSet` wire this convention into DRF viewsets.

## Common Auditable Serializers

`core.serializers.common` provides model serializer bases for auditable models:

- `AuditableModelSerializer` keeps audit fields available but marks them read-only.
- `ExcludeDeleteModelSerializer` hides soft-delete fields: `is_deleted`, `deleted`, and `deleted_by`.
- `ExcludeAuditableModelSerializer` hides both audit fields and soft-delete fields.

These bases reduce repeated `Meta.exclude` and `Meta.read_only_fields` definitions across inherited serializers. They combine their audit-related defaults with the serializer's own `Meta.exclude` and `Meta.read_only_fields` while preserving DRF's normal `fields` and `exclude` behavior.

Prefer defining `Meta.fields` explicitly for most serializers because it makes the public API shape clear. Use these bases when a serializer still needs inherited audit handling, especially when `Meta.exclude` is used. For example, `UserSerializer` inherits from `ExcludeDeleteModelSerializer` so API responses do not expose soft-delete metadata.

## API Call Flow

For a typical DRF viewset request:

1. Django routes `/api/...` through `config.urls` into `core.urls`, then into the resource URL module in `core/views`.
2. DRF resolves the viewset action from the HTTP method and route, for example `list`, `retrieve`, `create`, `update`, or a custom `@action`.
3. Authentication runs first. This starter kit uses Simple JWT via `JWTAuthentication`.
4. Permission classes run next. Examples include `DjangoModelPermissions`, `IsAuthenticated`, and custom classes from `permissions.factory.permissions_class(...)`.
5. The viewset starts from `get_queryset()` or the `queryset` attribute. This is where related objects should be optimized with `select_related()` or `prefetch_related()`.
6. For detail routes, `get_object()` applies the queryset, URL lookup, object permission checks, and returns the instance.
7. Filter backends apply `filterset_class` rules for list endpoints. The global default is `DjangoFilterBackend`.
8. Pagination is applied for list responses when the viewset has a pagination class.
9. `get_serializer_class()` chooses the serializer for the current action.
10. For write actions, the serializer receives request data, runs field validators, `validate_<field>()`, and `validate()`.
11. After `serializer.is_valid(raise_exception=True)`, the serializer `create()` or `update()` method persists changes.
12. `perform_create()` or `perform_update()` passes `performed_by=request.user` for auditable writes.
13. The response serializer data is rendered as camelCase JSON.

`UserViewSet` is the main example: it uses model permissions, a `UserFilter`, limit-offset pagination, action-specific serializers, custom self-service actions, password validation, avatar upload URL generation, and MinIO-backed file verification.

## Creating A Complete Viewset

When adding a new API resource, create the viewset as a thin orchestration layer and keep business validation in serializers or domain helpers.

1. Define the model and manager behavior in `core/models`. Use `AuditableModel` when the resource needs actor tracking and soft delete.
2. Add serializers in `core/serializers`: one read serializer, plus separate create/update/action serializers when write inputs differ from response shape. Prefer explicit `Meta.fields`; for auditable models that need shared audit handling, choose `AuditableModelSerializer`, `ExcludeDeleteModelSerializer`, or `ExcludeAuditableModelSerializer` as the base class.
3. Add reusable field validators in `core/validators` and serializer-level validation for checks that need request context, related models, or external services.
4. Add a `FilterSet` beside the viewset when list endpoints need query filters.
5. Create the viewset in `core/viewsets` using only the required DRF mixins, or `AuditableModelViewSet` for full CRUD on auditable models.
6. Set `queryset`, `permission_classes`, `serializer_class` or `get_serializer_class()`, `filterset_class`, and `pagination_class` explicitly.
7. Optimize the queryset for serializer access with `select_related()` and `prefetch_related()`.
8. For auditable writes, implement `perform_create()`, `perform_update()`, and `perform_destroy()` or use the auditable mixins.
9. Add custom operations with `@action`, including method, `detail`, `url_path`, action-specific permissions, validation, and response status.
10. Register the route in a file under `core/views` so `core.views.__init__` can collect it into `core.urls`.
11. Verify the endpoint in Swagger at `/api/schema/swagger/` and add tests when behavior includes permissions, filters, validation, or side effects.

Minimal pattern:

```python
class ExampleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = models.Example.objects.select_related("owner").all()
    permission_classes = [permissions.DjangoModelPermissions]
    filterset_class = ExampleFilter
    pagination_class = pagination.factory.limit_offset_class(maximum_limit=200)

    def get_serializer_class(self):
        match self.action:
            case "create":
                return serializers.ExampleCreateSerializer
            case "update" | "partial_update":
                return serializers.ExampleUpdateSerializer
            case _:
                return serializers.ExampleSerializer

    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(performed_by=self.request.user)
```

## Permissions

Permissions are exported from `core.permissions` so viewsets can import from one project namespace:

```python
permission_classes = [permissions.DjangoModelPermissions]
permission_classes = [permissions.IsAuthenticated]
permission_classes = [permissions.factory.permissions_class("auth.view_group")]
```

Use `DjangoModelPermissions` for model CRUD permissions and `permissions.factory.permissions_class(...)` when an endpoint needs a specific Django permission codename.

## Pagination

The global default is limit-offset pagination with page size `10` and max limit `100`:

```python
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "core.pagination.Max100LimitOffsetPagination",
    "PAGE_SIZE": 10,
}
```

For endpoint-specific limits, use the factory:

```python
pagination_class = pagination.factory.limit_offset_class(maximum_limit=200)
```

Set `pagination_class = None` for small fixed lists such as permission metadata.

## Mixins

`core.mixins` re-exports DRF's common model mixins and adds auditable mixins. Compose only the actions an endpoint supports:

```python
class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    ...
```

Use `AuditableModelViewSet` when a model supports the full CRUD surface and should automatically record the acting user.

## Validators

`core.validators` exposes Django validators, DRF uniqueness validators, and project validators from one namespace. Examples include:

- `ImageFileNameValidator` for safe image object names
- `ImageFileExtensionValidator` for uploaded image files
- `IntegerValidator`, `IntegerListValidator`
- `IPv4Validator`, `IPv6Validator`, `IPv4OrIPv6Validator`
- `SlugValidator`, `UnicodeSlugValidator`

Use serializer field validators for simple constraints and serializer `validate_*` methods for checks that need request context, database state, or external services.

## Background Task Scheduler

Huey is configured in `config.settings` and tasks live in `core/tasks`. Run the worker with:

```bash
python manage.py run_huey
```

The included `minio_garbage_collect` task runs daily at midnight and deletes orphaned pending `FileAsset` records and their MinIO objects after `FILE_ORPHANED_INTERVAL`.

With Docker Compose, the `worker` service runs Huey and the `server` service runs Gunicorn:

```bash
docker compose up --build
```

## Migrations

Create and apply schema migrations with standard Django commands:

```bash
python manage.py makemigrations
python manage.py migrate
```

The Docker Compose `migrate` service runs `python manage.py migrate --noinput` before the app and worker start.

## Data Dump And Load

Use Django fixtures for portable data snapshots:

```bash
python manage.py dumpdata core --indent 2 > core-fixture.json
python manage.py loaddata core-fixture.json
```

Useful variants:

```bash
python manage.py dumpdata core.User --indent 2 > users.json
python manage.py dumpdata --natural-foreign --natural-primary --indent 2 > data.json
```

Avoid dumping secrets, production credentials, tokens, or sensitive user data.

## Caching

Django cache is configured as dummy cache locally and Redis in production. `utils.cache` provides:

- `@cached(base_key, ttl, vary_on_args=True)` to cache function results.
- `clear_cache(base_key)` to invalidate all variants for a base key by bumping its version.
- `delete_cache(...)` to delete one exact cached call.

Cache keys are stable across equivalent positional and keyword calls by binding arguments to the function signature before hashing.

## Object Storage

`integrations.minio` wraps the MinIO client and supports:

- direct upload and download
- object stat checks
- presigned upload URLs
- presigned private downloads
- public object URLs
- bulk delete

The avatar flow demonstrates the pattern: create a pending `FileAsset`, return a presigned upload URL, validate the uploaded object with MinIO, attach it to the user, and mark the file as ready.

## Common Commands

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py run_huey
```

For local infrastructure:

```bash
docker compose up --build
```
