# DRF Start Kit

A starter kit for building APIs with Django REST Framework. It provides a ready-to-extend project layout with JWT authentication, model permissions, filtering, pagination, auditable models, reusable validators, background jobs, caching helpers, OpenAPI documentation, and MinIO object storage integration.

| Resource | URL |
|----------|-----|
| API root | `/api/` |
| Swagger UI | `/api/schema/swagger/` (hidden in `PRODUCTION`) |
| Health check | `/api/health/` |
| JWT obtain | `POST /api/token/` |
| JWT refresh | `POST /api/token/refresh/` |
| JWT logout | `POST /api/token/logout/` |
| Current user permissions | `GET /api/users/me/permissions/` |

## Table of Contents

**Get started**

- [Quick Start](#quick-start)
- [Configuration](#configuration)

**Extend the codebase**

- [Project Structure](#project-structure)
- [Coding Conventions](#coding-conventions)
- [Creating a Complete Viewset](#creating-a-complete-viewset)
- [Auditable Models and Serializers](#auditable-models-and-serializers)
- [System actor](#system-actor)

**Reference**

- [DRF Reference](#drf-reference)
- [API Call Flow](#api-call-flow)
- [Authentication](#authentication)
- [Integrations](#integrations)
- [Operations](#operations)

**Appendix**

- [Internationalization](#internationalization)
- [Audit trail / event log (example)](#audit-trail--event-log-example)
- [Code formatting (Ruff)](#code-formatting-ruff)

Documentation is ordered for extending the starter kit: run and configure first, then project conventions and patterns, then runtime reference, then optional topics in the appendix.

## Quick Start

**Prerequisites:** Python 3.14+, Docker (optional), Postgres, Redis, and MinIO for full local parity with production. The development script can install GNU gettext for local translation compilation when a supported package manager is available.

### Docker (recommended)

Starts the app, Huey worker, Postgres, Redis, and MinIO. Migrations run automatically via the `migrate` service.

```bash
bash dev.sh
```

Open Swagger at [http://localhost:8000/api/schema/swagger/](http://localhost:8000/api/schema/swagger/) when `ENV` is not `PRODUCTION`.

### Local Python

```bash
bash dev.sh local
python manage.py createsuperuser
python manage.py runserver
```

Run the background worker in a second terminal:

```bash
python manage.py run_huey
```

Load bundled fixtures when you add seed data under `core/fixtures/`:

```bash
python manage.py loaddata core/fixtures/group.json core/fixtures/user.json
```

`bash dev.sh` and `bash dev.sh local` are safe to rerun. The script checks for existing setup such as `.env`, `.venv`, and GNU gettext before creating or installing anything. The generated `.env` uses development defaults; review it before using it outside local development.

## Configuration

Settings are loaded from environment variables via `env.py` (uses `python-dotenv`). Docker Compose reads a `.env` file at the project root.

| Variable | Required | Notes |
|----------|----------|-------|
| `DB_URL` | yes | Postgres URL, e.g. `postgresql://user:pass@localhost:5432/dbname` |
| `SECRET_KEY` | yes | Django secret key |
| `ENV` | no | `LOCAL` (default), `STAGING`, or `PRODUCTION` |
| `REDIS_URL` | STAGING, PRODUCTION | Required when `ENV` is not `LOCAL`; used for caching |
| `MINIO__ENDPOINT` | for file features | Host and port, e.g. `localhost:9000` |
| `MINIO__ACCESS_KEY` | for file features | MinIO access key |
| `MINIO__SECRET_KEY` | for file features | MinIO secret key |
| `MINIO__PUBLIC_BUCKET` | for file features | Public bucket name |
| `MINIO__PRIVATE_BUCKET` | for file features | Private bucket name |
| `MINIO__PUBLIC_URL` | no | Public base URL; defaults to `http(s)://{MINIO__ENDPOINT}` from `MINIO__SECURE` |
| `MINIO__SECURE` | no | Use HTTPS for MinIO client (`true`/`false`, default `false`) |
| `ALLOWED_HOSTS` | STAGING, PRODUCTION | Comma-separated hosts |
| `ALLOWED_ORIGINS` | STAGING, PRODUCTION | Comma-separated CORS origins (see note below) |
| `LANGUAGE_CODE` | no | Default API language when no request preference matches; defaults to `vi` |
| `HUEY_WORKERS` | no | Huey consumer thread count (default `6`) |

Example `.env` for local development alongside `docker compose`:

```env
ENV=LOCAL
DB_URL=postgresql://postgres:postgres@localhost:5432/postgres
SECRET_KEY=change-me-in-production
REDIS_URL=redis://localhost:6379
MINIO__ENDPOINT=localhost:9000
MINIO__ACCESS_KEY=minioadmin
MINIO__SECRET_KEY=minioadmin
MINIO__PUBLIC_BUCKET=public
MINIO__PRIVATE_BUCKET=private
MINIO__SECURE=false
```

Name service-specific variables with double underscores (`MINIO__*`). Keep shared settings simple (`DB_URL`, `SECRET_KEY`, `REDIS_URL`).

**Environment behaviour**

| `ENV` | `DEBUG` | Cache | Swagger UI | CORS |
|-------|---------|-------|------------|------|
| `LOCAL` | on | dummy | yes | allow all origins |
| `STAGING` | off | Redis | yes | allow all origins (test environment) |
| `PRODUCTION` | off | Redis | hidden | `ALLOWED_ORIGINS` only |

When `ENV` is not `PRODUCTION`, `CORS_ALLOW_ALL_ORIGINS` is enabled so LOCAL and STAGING stay easy to test against arbitrary front-end dev servers. Production restricts origins to `ALLOWED_ORIGINS`.

## Project Structure

```text
config/                 Django project settings, ASGI/WSGI, root URLs
core/                   Main application package
  models/               Domain models and shared model base classes
  serializers/          DRF serializers grouped by resource
  viewsets/             DRF viewsets and action routing
  views/                URL registration (auth, health, routers)
  permissions/          Permission exports and permission factories
  pagination/           Pagination classes and factories
  mixins/               DRF and auditable model mixins
  validators/           Django, DRF, and project validators
  usecases/             Optional write orchestration for complex business flows
  services/             Optional reusable domain and infrastructure helpers
  tasks/                Huey background and periodic tasks
  fixtures/             Django fixture files for seed data
  migrations/           Django schema migrations
integrations/           External service clients, for example MinIO
i18n/                   Third-party translation override msgids
locale/                 Django translation catalogs
utils/                  Shared helpers such as cache and logging
manage.py               Django management entry point
docker-compose.yml      Local services: app, worker, Postgres, Redis, MinIO
```

`core.views.__init__` automatically imports URL modules and collects their `url_patterns`, so adding a new file under `core/views/` registers endpoints without editing a central list.

Registered URL modules today: `auth`, `health`, `user`, `group`, `permission`.

## Coding Conventions

- Keep each resource split by layer: model in `core/models`, serializer in `core/serializers`, viewset in `core/viewsets`, and URL registration in `core/views`.
- Prefer `ModelViewSet` for standard full CRUD. Use `AuditableModelViewSet` when the model extends `AuditableModel`. Use `GenericViewSet` with explicit mixins only when an endpoint supports a subset of actions (for example list-only) or omits standard mixins in favor of custom `@action` handlers (for example `UserViewSet`).
- Put request validation in serializers and reusable field validation in `core/validators`.
- Prefer explicit `Meta.fields` in serializers so the API contract is easy to review. For auditable models, inherit from bases in `core.serializers.common` instead of repeating audit `exclude` and `read_only_fields`.
- Use `get_serializer_class()` when different actions need different read/write serializers.
- Pass `performed_by=request.user` when creating, updating, or deleting auditable models (see [Auditable Models and Serializers](#auditable-models-and-serializers)).
- Use `select_related()` and `prefetch_related()` on viewset querysets when serializers access related objects.
- APIs use camelCase JSON through `djangorestframework-camel-case`; Python code stays snake_case.
- Import through `core` package modules that re-export shared symbols instead of pulling the same names from upstream libraries. Inside `core`, use relative package imports and access symbols on those namespaces — for example `from .. import models`, `serializers`, `validators`, `permissions`, `pagination`, and `mixins`, then `permissions.DjangoModelPermissions`, `validators.MinValueValidator`, `serializers.ModelSerializer`. The package `__init__.py` files own the re-exports from Django, DRF, and project code; resource modules (viewsets, serializers, and so on) should not import re-exported symbols directly from `rest_framework.*` or `django.core.validators` when they are available on a `core` package.
- Group imports in this order: standard library, third-party packages (only symbols not re-exported by `core`, such as `rest_framework.status` or `django.db.transaction`), then local `core` package imports.
- Keep simple writes in serializers (`create` / `update`, `validate_*`). Use `core/usecases` and `core/services` only when a flow needs multi-entity transactions, reuse from tasks or commands, or business logic that outgrows a single serializer. GET/list/retrieve stay in viewsets and querysets.

## Use Cases and Services

For most endpoints, DRF serializers are enough. Add layers when you see at least one of these signals:

- One write touches multiple entities inside a single transaction
- The same logic must run from an API endpoint and a background task or management command
- Serializer `create` / `update` is becoming hard to read or test

Suggested layout:

```text
core/usecases/<flow>.py     orchestration, @transaction.atomic at the outer boundary
core/services/<entity>.py     focused entity or infrastructure operations
core/services/common/         shared helpers (files, notifications, ...)
```

Call direction:

```text
viewset -> serializer (validate) -> usecase (optional) -> service (optional) -> model
```

Do not route simple CRUD through use cases just for consistency. Read endpoints do not need use cases.

## Creating a Complete Viewset

When adding a new API resource, create the viewset as a thin orchestration layer and keep business validation in serializers or domain helpers.

1. Define the model and manager behavior in `core/models`. Use `AuditableModel` when the resource needs actor tracking and soft delete.
2. Add serializers in `core/serializers`: one read serializer, plus separate create/update/action serializers when write inputs differ from response shape.
3. Add reusable field validators in `core/validators` and serializer-level validation for checks that need request context, related models, or external services.
4. Add a `FilterSet` beside the viewset when list endpoints need query filters.
5. Create the viewset in `core/viewsets`: `ModelViewSet` or `AuditableModelViewSet` for full CRUD; otherwise `GenericViewSet` with only the mixins you need.
6. Set `queryset`, `permission_classes`, `serializer_class` or `get_serializer_class()`, `filterset_class`, and `pagination_class` explicitly.
7. Optimize the queryset for serializer access with `select_related()` and `prefetch_related()`.
8. For auditable writes, implement `perform_create()`, `perform_update()`, and `perform_destroy()` or use the auditable mixins.
9. Add custom operations with `@action`, including method, `detail`, `url_path`, action-specific permissions, validation, and response status.
10. Register the route in a file under `core/views` so `core.views.__init__` can collect it into `core.urls`.
11. Verify the endpoint in Swagger and add tests when behavior includes permissions, filters, validation, or side effects.

`UserViewSet` is the main reference: `DjangoModelPermissions`, queryset scoping without `core.view_user`, `UserFilter`, limit-offset pagination, action-specific serializers, self-service endpoints, password validation, avatar presigned upload URLs, and MinIO-backed file verification.

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

## Auditable Models and Serializers

### Models

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

`AuditableModel.save()` (`core/models/common/audit.py`) requires `performed_by`, stamps `created_by` on insert and `updated_by` on update, then delegates to Django's `Model.save()`.

Custom serializer `create()` / `update()` methods must `pop('performed_by')` from `validated_data` and forward it to `instance.save(performed_by=...)` or `Model.objects.create(..., performed_by=...)`.

When no real user exists (commands, tasks, fixtures), use [`SYSTEM_ACTOR`](#system-actor) instead of `request.user`. See [System actor](#system-actor) for usage rules.

### Viewset mixins

`CreateAuditableModelMixin`, `UpdateAuditableModelMixin`, and `DestroyAuditableModelMixin` call `serializer.save(performed_by=self.request.user)` or `instance.delete(performed_by=self.request.user)`.

Use `AuditableModelViewSet` for full CRUD on auditable models with actor tracking wired in automatically.

### Serializer bases

`core.serializers.common` provides model serializer bases:

| Base | Behavior |
|------|----------|
| `AuditableModelSerializer` | Audit fields available but read-only |
| `ExcludeDeleteModelSerializer` | Hides `is_deleted`, `deleted`, `deleted_by` |
| `ExcludeAuditableModelSerializer` | Hides all audit and soft-delete fields |

Prefer explicit `Meta.fields` for most serializers. Use these bases when a serializer needs inherited audit handling, especially with `Meta.exclude`. For example, `UserSerializer` inherits from `ExcludeDeleteModelSerializer` so API responses do not expose soft-delete metadata.

## System actor

Auditable models require `performed_by` on every write. HTTP viewsets pass `request.user`; offline flows (management commands, Huey tasks, fixtures, migrations) have no caller.

`core/constants.py` exports `SYSTEM_ACTOR` — an **unsaved** `User(username='system')`. It is never inserted into the database. Audit fields store the string `'system'` via `performed_by.username`.

### When to use

| Context | Actor |
|---------|--------|
| Viewset / API handler | `request.user` |
| Serializer called from a viewset | `serializer.save(performed_by=request.user)` |
| Management command | `SYSTEM_ACTOR` |
| Huey periodic or background task | `SYSTEM_ACTOR` |
| Fixture load / bootstrap script | `SYSTEM_ACTOR` |
| `createsuperuser` | `SYSTEM_ACTOR` (default in `_UserManager.create_superuser`) |

### How to use

Import once and pass as `performed_by` on any auditable write:

```python
from core.constants import SYSTEM_ACTOR

# create
User.objects.create_user(username='bot', password='...', performed_by=SYSTEM_ACTOR)

# update
instance.save(performed_by=SYSTEM_ACTOR)
User.objects.filter(pk=instance.pk).update(is_active=False, performed_by=SYSTEM_ACTOR)

# soft delete
instance.delete(performed_by=SYSTEM_ACTOR)
```

In a management command:

```python
from django.core.management.base import BaseCommand
from core.constants import SYSTEM_ACTOR
from core.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        User.objects.create_user(
            username='service',
            password='...',
            performed_by=SYSTEM_ACTOR,
        )
```

In a Huey task:

```python
from core.constants import SYSTEM_ACTOR

@djhuey.db_task()
def reconcile_records():
    for row in queryset:
        row.save(performed_by=SYSTEM_ACTOR)
```

### Do not use for

- `login()`, session auth, or anything that treats `performed_by` as `request.user`
- Permission checks (`user.has_perm(...)`, `DjangoModelPermissions`)
- Foreign keys or relations that expect a saved `User` row

For those cases, load or create a real user in the database.

### Sentinel pattern (optional)

The project uses an unsaved `User` because `_validate_performed_by` expects an object with `username`. If you want to avoid touching the ORM model at all, replace `SYSTEM_ACTOR` with a minimal sentinel that exposes the same attribute — for example:

```python
from types import SimpleNamespace

SYSTEM_ACTOR = SimpleNamespace(username='system')
```

Only do this if every call site reads `performed_by.username` and never passes the actor into Django auth APIs.

## DRF Reference

### Permissions

Exported from `core.permissions`:

```python
permission_classes = [permissions.DjangoModelPermissions]
permission_classes = [permissions.IsAuthenticated]
permission_classes = [permissions.factory.permissions_class("auth.view_group")]
```

Use `DjangoModelPermissions` for model CRUD permissions and `permissions.factory.permissions_class(...)` for a specific Django permission codename.

With stock DRF `DjangoModelPermissions`, safe methods (`GET`, `HEAD`, `OPTIONS`) require an authenticated user but **no** Django model permission codename. Unsafe methods map to `add` / `change` / `delete`. `UserViewSet` additionally uses `core.view_user` in `get_queryset()` to decide whether list/retrieve spans all users or only `request.user`.

### Pagination

Global default: limit-offset pagination, page size `10`, max limit `100`.

```python
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "core.pagination.Max100LimitOffsetPagination",
    "PAGE_SIZE": 10,
}
```

Per-endpoint limits:

```python
pagination_class = pagination.factory.limit_offset_class(maximum_limit=200)
```

Set `pagination_class = None` for small fixed catalog endpoints such as `GET /api/permissions/` (global permission list).

### Filtering, search, and ordering

This project enables these filter backends globally (see `config/settings.py`):

- `DjangoFilterBackend` — structured query filters via `filterset_class`
- `SearchFilter` — free-text search via `?search=...`
- `OrderingFilter` — ordering via `?ordering=field` / `?ordering=-field`

Usage guidelines:

- **Structured filters**: define a `django_filters.FilterSet` next to the viewset and set `filterset_class`.
  - Example: `is_active=true`, `groups=<id>` on list endpoints that support those filters.
- **Search**: set `search_fields = [...]` on the viewset.
  - Example: `GET /api/users/?search=admin`
- **Ordering**: set `ordering_fields = [...]` and (optionally) default `ordering = [...]`.
  - Example: `GET /api/users/?ordering=-date_joined`

Prefer `FilterSet` for typed filters (booleans, dates, FK/M2M ids) and reserve `?search=` for text matching.

### Mixins

`core.mixins` re-exports DRF model mixins (`ListModelMixin`, `CreateModelMixin`, etc.) and auditable mixins. Default to `ModelViewSet` or `AuditableModelViewSet` for full CRUD; compose explicit mixins on `GenericViewSet` when you need a subset of actions.

### Validators

Import validators from `core.validators` (inside `core`, `from .. import validators`). Do not import re-exported symbols directly from `django.core.validators` or `rest_framework.validators`.

**Commonly used (Django, re-exported):**

| Validator | Typical use |
|-----------|-------------|
| `MinValueValidator` / `MaxValueValidator` | Numeric bounds (integers, decimals) |
| `MinLengthValidator` / `MaxLengthValidator` | String or list length |
| `EmailValidator` | Email-shaped strings |
| `URLValidator` | URL-shaped strings |
| `RegexValidator` | Custom pattern match |
| `FileExtensionValidator` | Allowed file extensions |
| `DecimalValidator` | Decimal max digits / decimal places |
| `StepValueValidator` | Numeric step (for example multiples of 0.01) |
| `ProhibitNullCharactersValidator` | Reject `\x00` in strings |
| `DomainNameValidator` | Domain name format |

**Uniqueness (DRF, re-exported):**

| Validator | Typical use |
|-----------|-------------|
| `UniqueValidator` | Field unique within a queryset |
| `UniqueTogetherValidator` | Composite uniqueness |
| `UniqueForDateValidator` / `UniqueForMonthValidator` / `UniqueForYearValidator` | Time-scoped uniqueness |

**Project validators (`core.validators.common`):**

| Validator | Typical use |
|-----------|-------------|
| `FileSizeValidator` | Byte size bounds; omitted `max_size` uses `settings.FILE_UPLOAD_MAX_MEMORY_SIZE`; `max_size=None` removes the upper bound |
| `ImageFileNameValidator` | Safe image object names (fixed image extensions) |
| `DocumentFileNameValidator` | Document names; pass an explicit extension allowlist, e.g. `['pdf', 'docx']` |
| `ImageFileExtensionValidator` | Uploaded image file extensions |
| `PhoneNumberValidator` | E.164 phone numbers (`+84901234567`) |
| `HexColorValidator` | `#fff` or `#1a2b3c` colors |
| `IntegerValidator` / `IntegerListValidator` | Integer or comma-separated integer lists |
| `IPv4Validator` / `IPv6Validator` / `IPv4OrIPv6Validator` | IP address format |
| `SlugValidator` / `UnicodeSlugValidator` | Slug format |

Example on a serializer field:

```python
from .. import validators

file_size = serializers.IntegerField(
    validators=[validators.FileSizeValidator()],
)
file_name = serializers.CharField(validators=[validators.ImageFileNameValidator()])
document_name = serializers.CharField(
    validators=[validators.DocumentFileNameValidator(['pdf', 'docx'])],
)

class UserPreferencesSerializer(serializers.Serializer):
    theme = serializers.CharField()
    languague = serializers.CharField()

preferences = UserPreferencesSerializer(required=False)
```

Use nested serializers for structured JSON objects so DRF can return field-level errors. Use field validators for simple constraints and serializer `validate_*` / `validate()` for checks that need request context, database state, or external services.

## API Call Flow

Every `/api/...` request passes through Django middleware, URL routing, DRF view dispatch, and (for writes) serializer validation before data reaches the ORM. Diagrams render on GitHub, in VS Code/Cursor Markdown preview, and in any tool that supports [Mermaid](https://mermaid.js.org/).

For auditable write conventions, see [Auditable Models and Serializers](#auditable-models-and-serializers).

### Request entry and dispatch

```mermaid
flowchart TD
    MW["LoggingMiddleware.__call__<br/>core/middlewares/log.py"]
    URL["URL resolve → router → ViewSet.as_view<br/>config/urls.py → core/views/"]
    DISPATCH["APIView.dispatch<br/>rest_framework/views.py"]
    INIT["initialize_request + initial<br/>JWT auth, permissions, throttles"]
    HANDLER["Action handler<br/>list / retrieve / create / update / destroy / @action"]
    RENDER["finalize_response → CamelCaseJSONRenderer"]

    MW --> URL --> DISPATCH --> INIT --> HANDLER --> RENDER
```

`ViewSetMixin.as_view()` binds HTTP methods to actions (for example `POST /api/users/` → `create`). `APIView.dispatch()` runs `initial()` for authentication and permissions, calls the action handler, then renders camelCase JSON.

### Read actions (`GET`)

```mermaid
flowchart LR
    subgraph list ["List — GET /api/users/"]
        L1["filter_queryset(get_queryset())"]
        L2["paginate_queryset() optional"]
        L3["get_serializer(many=True)"]
        L4["Response(serializer.data)"]
        L1 --> L2 --> L3 --> L4
    end

    subgraph retrieve ["Retrieve — GET /api/users/{id}/"]
        R1["get_object()"]
        R2["get_serializer(instance)"]
        R3["Response(serializer.data)"]
        R1 --> R2 --> R3
    end
```

Use `select_related()` / `prefetch_related()` in `get_queryset()`. List endpoints apply `filterset_class` through `DjangoFilterBackend`.

### Write actions — `UserViewSet` examples

Create and update share the same validation pipeline (`is_valid` → `run_validation` → `to_internal_value` → `validate_<field>` → `validate`). They diverge at `Serializer.save()` when an instance already exists.

**Create** — `POST /api/users/`

```mermaid
flowchart TD
    subgraph drf ["DRF mixin"]
        C1["CreateModelMixin.create"]
        C2["get_serializer(data=request.data)<br/>→ UserCreateSerializer"]
    end

    subgraph validate ["Serializer validation"]
        V1["is_valid(raise_exception=True)"]
        V2["run_validation"]
        V3["to_internal_value — per field"]
        V4["validate_<field> optional"]
        V5["validate(attrs)"]
        V1 --> V2 --> V3 --> V4 --> V5
    end

    subgraph persist ["ViewSet → ORM"]
        P1["perform_create<br/>serializer.save(performed_by=user)"]
        P2["Serializer.save merges kwargs"]
        P3["UserCreateSerializer.create"]
        P4["_UserManager._create_user"]
        P5["AuditableModel.save"]
        P6["Model.save → SQL INSERT"]
        P7["groups.set() M2M"]
        P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7
    end

    RESP["Response(serializer.data, 201)"]

    C1 --> C2 --> V1
    V5 --> P1
    P7 --> RESP
```

Notable steps: `perform_create` passes `performed_by`; custom `UserCreateSerializer.create` pops M2M `groups` before `create_user`; `AuditableModel.save` stamps audit fields. Stock `ModelViewSet` serializers (for example `GroupViewSet`) use default `ModelSerializer.create()` → `objects.create(**validated_data)`.

**Update** — `PATCH /api/users/{id}/`

```mermaid
flowchart TD
    U1["UpdateModelMixin.update"]
    U2["get_object()"]
    U3["get_serializer(instance, data, partial)"]
    U4["is_valid → run_validation → validate"]
    U5["perform_update → serializer.save(performed_by=user)"]
    U6["UserUpdateSerializer.update"]
    U7["AuditableModel.save → SQL UPDATE"]
    U8["Response(serializer.data, 200)"]

    U1 --> U2 --> U3 --> U4 --> U5 --> U6 --> U7 --> U8
```

**Destroy** — `DELETE /api/users/{id}/`

```mermaid
flowchart LR
    D1["DestroyModelMixin.destroy"] --> D2["get_object()"] --> D3["perform_destroy(instance)"]
    D3 --> D4["instance.delete(performed_by=user)<br/>soft delete"]
```

Use `DestroyAuditableModelMixin` or `AuditableModelViewSet` for soft delete on auditable models.

### Custom `@action` handlers

Custom actions (for example `UserViewSet.update_self`) call the serializer steps explicitly:

`get_serializer(instance, data=...)` → `is_valid(raise_exception=True)` → `save(performed_by=request.user)` → `Response(...)`.

`serializer.save(**extra)` merges `extra` into `validated_data` before `create()` or `update()`.

## Authentication

JWT auth uses `rest_framework_simplejwt` with token blacklist support. Token obtain and refresh endpoints are throttled to `5/minute` per IP.

**Obtain tokens** — `POST /api/token/` with JSON body (camelCase keys accepted):

```json
{ "username": "admin", "password": "..." }
```

**Refresh** — `POST /api/token/refresh/` with `{ "refresh": "..." }`.

**Logout** — `POST /api/token/logout/` with `{ "refresh": "..." }` to blacklist the refresh token.

Self-service password change (`PUT /api/users/me/password/`) and avatar presigned upload (`POST /api/users/me/avatar/presigned-upload-url/`) are throttled to `10/minute` per authenticated user.

Token payload claims are camelized to match API JSON (`core/serializers/auth.py`). Send the access token on protected requests:

```http
Authorization: Bearer <access_token>
```

Protected viewsets default to `JWTAuthentication`. Use `permission_classes = [permissions.IsAuthenticated]` or `DjangoModelPermissions` on viewsets as needed.

**JWT lifetimes** — access token lifetime is `30 days` when `DEBUG` is on (`ENV=LOCAL`) and `5 minutes` otherwise. Refresh token lifetime is `7 days`. Rotation and blacklist on refresh are enabled.

## Integrations

### Object storage

`integrations.minio` wraps the MinIO client:

- direct upload and download
- object stat checks
- presigned upload URLs
- presigned private downloads
- public object URLs
- bulk delete

The avatar flow in `UserViewSet` demonstrates the pattern: create a pending `FileAsset`, return a presigned upload URL, validate the uploaded object with MinIO, attach it to the user, and mark the file as ready.

Reusable serializers live in `core/serializers/common/file.py`:

| Serializer | Role |
|------------|------|
| `FilePresignedUploadUrlSerializer` | Create pending `FileAsset`, return presigned upload URL |
| `FileAttachSerializer` | Validate uploaded object in MinIO and attach to a model |

Subclass with `is_public` or override fields for endpoint-specific rules. `UserAvatarUploadUrlSerializer` sets `is_public` and validates `file_name` with `ImageFileNameValidator`. `UserAvatarSelfUpdateSerializer` sets `field_name` and attaches via the shared attach flow.

### Caching

Django cache is dummy cache when `DEBUG` is on (`ENV=LOCAL`) and Redis when `DEBUG` is off (`STAGING`, `PRODUCTION`). `utils.cache` provides:

- `@cached(base_key, ttl, vary_on_args=True)` to cache function results
- `clear_cache(base_key)` to invalidate all variants for a base key
- `delete_cache(...)` to delete one exact cached call

Cache keys are stable across equivalent positional and keyword calls by binding arguments to the function signature before hashing.

### Background tasks

Huey is configured in `config.settings`; tasks live in `core/tasks`. Consumer worker count is set by `HUEY_WORKERS` (default `6`) in `HUEY["consumer"]["workers"]`.

The `minio_garbage_collect` task runs daily at midnight and deletes orphaned pending `FileAsset` records and their MinIO objects after `FILE_ORPHANED_INTERVAL`.

The `flush_expired_tokens` task runs daily at 03:30 UTC and deletes expired rows from the JWT blacklist `OutstandingToken` table (same effect as `python manage.py flushexpiredtokens`).

Docker Compose runs the worker via the `worker` service (`python manage.py run_huey`). Run it manually when not using Docker:

```bash
python manage.py run_huey
```

## Operations

### Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

Docker Compose runs `migrate --noinput` automatically before the app and worker start.

### Fixtures

```bash
python manage.py loaddata core/fixtures/group.json core/fixtures/user.json
python manage.py dumpdata core --indent 2 > core-fixture.json
```

Avoid dumping secrets, production credentials, tokens, or sensitive user data.

## Appendix

### Internationalization

DRF uses Django's translation system for built-in exception and serializer validation messages. This project enables per-request language negotiation with `django.middleware.locale.LocaleMiddleware`, so API clients can set `Accept-Language`, for example:

```http
Accept-Language: vi
Accept-Language: en
```

Supported languages are configured in `config/settings.py` as Vietnamese (`vi`) and English (`en`). The default comes from `LANGUAGE_CODE` and falls back to `vi`.

Project-owned user-facing strings should be wrapped with `gettext_lazy`:

```python
from django.utils.translation import gettext_lazy as _

raise serializers.ValidationError(_("File does not exist."))
```

Third-party message overrides live under `i18n/`, grouped by source package such as `drf.py` and `simplejwt.py`. Add new plugin overrides in a dedicated module so `makemessages` keeps those `msgid`s in the project catalog without patching installed packages.

Translation catalogs live under `locale/`. Commit only the `.po` source files; `.mo` files are compiled locally or during Docker build and are not tracked in git. After adding or changing translated strings, refresh and compile catalogs:

```bash
python manage.py makemessages -l vi
python manage.py compilemessages
```

Docker builds compile catalogs automatically. For local development, install a current GNU gettext so Django can find compatible `msgfmt` and `msgmerge` commands. On Windows, prefer `winget install --id mlocati.GetText -e`; the older GnuWin32 gettext package does not support Django's `makemessages` options.

### Audit trail / event log (example)

`AuditableModel` stores who changed a row and when, but not *what* changed. For a separate activity feed or compliance log, add an append-only event model and write to it from serializers or signals.

Example model:

```python
class AuditEvent(models.Model):
    actor = models.CharField(max_length=150)
    action = models.CharField(max_length=50)  # create, update, delete
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=64)
    changes = models.JSONField(default=dict)  # {"field": {"old": "...", "new": "..."}}
    created = models.DateTimeField(auto_now_add=True, db_index=True)
```

Example write helper inside a serializer `update()`:

```python
def log_event(*, actor, action, instance, changes):
    AuditEvent.objects.create(
        actor=actor.username,
        action=action,
        resource_type=instance._meta.label_lower,
        resource_id=str(instance.pk),
        changes=changes,
    )
```

Example read-only API:

```python
class AuditEventViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = AuditEvent.objects.all().order_by("-created")
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.factory.permissions_class("core.view_auditevent")]
    filterset_fields = ["resource_type", "resource_id", "actor"]
```

Use nested routes such as `/api/users/{id}/audit-events/` when the log is scoped to one resource, instead of embedding events in paginated list responses.

### Code formatting (Ruff)

[`pyproject.toml`](pyproject.toml) configures [Ruff](https://docs.astral.sh/ruff/) for import sorting (`I`) and formatting.

Install and run manually:

```bash
pip install ruff
ruff check --fix .
ruff format .
```

Format on save in Cursor/VS Code: install the Ruff extension, then add to `.vscode/settings.json`:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

OpenAPI schema and Swagger UI routes are registered only when `ENV` is not `PRODUCTION`.
