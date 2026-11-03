# DRF Start Kit

A starter layout for Django REST Framework APIs. Each resource lives in its own app. Shared audit bases live in `shared_kernel`. DRF helpers live in `extensions`.

JWT authentication, groups, filtering, pagination, auditable models, validators, Huey jobs, Redis caching, OpenAPI, and MinIO uploads are wired in. Views are public until they set `permission_classes`. The task queue is Huey stored in Postgres. Redis is only the cache.

JSON keys are camelCase. Python stays snake_case.

## Routes

Mounted from `config/urls.py`.

| Resource | URL |
|----------|-----|
| API root | `/api/` redirects to Swagger outside production |
| Swagger UI | `/api/schema/swagger/` (omitted when `ENV=PRODUCTION`) |
| OpenAPI schema | `/api/schema/` (omitted when `ENV=PRODUCTION`) |
| Liveness | `GET /api/health/live/` |
| Readiness | `GET /api/health/ready/` |
| JWT obtain | `POST /api/token/` |
| JWT refresh | `POST /api/token/refresh/` |
| JWT logout | `POST /api/token/logout/` |
| Password reset request | `POST /api/password-reset/` |
| Password reset confirm | `POST /api/password-reset/confirm/` |
| Users | `/api/users/` |
| Current user | `GET /api/users/me/` and `PATCH /api/users/me/` |
| Groups | `/api/groups/` |
| Permissions | `GET /api/permissions/` |
| Group permissions | `GET /api/groups/{id}/permissions/` |
| Notifications | `GET /api/notifications/`, `POST /api/notifications/{id}/mark-as-read/`, `POST /api/notifications/mark-all-as-read/` |
| Logs | `GET /api/logs/` |

## Quick start

**Prerequisites:** Python 3.13+, Postgres. Docker Compose also starts Redis, MinIO, the API, and the Huey worker. Redis is unused while `ENV=LOCAL` because the cache backend is the dummy cache. MinIO is required only for file uploads.

### Docker

```bash
bash dev.sh
```

`dev.sh` creates a `.env` when one is missing, then runs `docker compose up --build`. The `migrate` service runs `migrate` on the default database and on `--database=logs`.

`dev.sh` writes `ROOT_USERNAME=root` and a random base64 `ROOT_PASSWORD` into a new `.env`, then prints the plaintext password once. An existing `.env` is left as it is. Settings will not import if either value is missing. `env.example` uses the base64 form of `change-me`.

Open Swagger at [http://localhost:8000/api/schema/swagger/](http://localhost:8000/api/schema/swagger/) when `ENV` is not `PRODUCTION`.

### Local Python

```bash
bash dev.sh local
python manage.py runserver
```

Run the worker in a second terminal. Periodic tasks do not run inside `runserver`.

```bash
python manage.py run_huey
```

Install dependencies yourself when you are not using `dev.sh local`:

```bash
python -m venv .venv
source .venv/bin/activate    # Windows Git Bash: source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

Pin direct dependencies in `requirements.txt` with `==`. Apply migrations to both databases:

```bash
python manage.py migrate
python manage.py migrate --database=logs
```

`createsuperuser` works. `post_migrate` ensures the root user from `ROOT_USERNAME` / `ROOT_PASSWORD`. When that row already exists, migrate sets its password from the environment again. That reset is intentional: the environment is the source for the root password.

## Configuration

`env.py` loads a `.env` file with `python-dotenv`. Compose reads the same file and overrides `DB_URL`, `REDIS_URL`, and the MinIO host for containers.

| Variable | Required | Notes |
|----------|----------|-------|
| `DB_URL` | yes | Postgres URL, for example `postgresql://user:pass@localhost:5432/dbname` |
| `SECRET_KEY` | yes | Django secret key |
| `ROOT_USERNAME` | yes | Username created or updated on migrate |
| `ROOT_PASSWORD` | yes | Base64-encoded password for that user. This is encoding, not encryption |
| `ENV` | no | `LOCAL` (default), `STAGING`, or `PRODUCTION` |
| `REDIS_URL` | staging and production | Cache only. Not the Huey broker. Omitted in `LOCAL` |
| `MINIO__ENDPOINT` | for files | Host and port, for example `localhost:9000` |
| `MINIO__ACCESS_KEY` | for files | MinIO access key |
| `MINIO__SECRET_KEY` | for files | MinIO secret key |
| `MINIO__PUBLIC_BUCKET` | for files | Public bucket |
| `MINIO__PRIVATE_BUCKET` | for files | Private bucket |
| `MINIO__PUBLIC_URL` | no | Browser-facing base URL. Defaults from `MINIO__SECURE` and `MINIO__ENDPOINT` |
| `MINIO__SECURE` | no | `true` or `false`. Default `false` |
| `MINIO__REGION` | no | SigV4 region. Default `us-east-1` |
| `FRONTEND_URL` | no | Origin used in password-reset links. Default `http://localhost:3000` |
| `EMAIL__HOST` | for SMTP | Empty in `LOCAL` sends mail to the console backend |
| `EMAIL__PORT` | no | Default `587` |
| `EMAIL__HOST_USER` | no | SMTP username |
| `EMAIL__HOST_PASSWORD` | no | SMTP password |
| `EMAIL__USE_TLS` | no | Default `true` |
| `EMAIL__FROM` | no | `DEFAULT_FROM_EMAIL`. Default `noreply@example.com` |
| `ALLOWED_HOSTS` | outside local | Comma-separated. Default `*` when `ENV` is not `LOCAL` |
| `ALLOWED_ORIGINS` | production | Comma-separated CORS origins. Default `http://localhost:3000` outside local |
| `LANGUAGE_CODE` | no | Default `vi` |
| `HUEY_WORKERS` | no | Huey thread count. Default `6`. Must be at least 1 |
| `LOG_RETENTION` | no | Days to keep log rows and log files. Default `60` |
| `GUNICORN_WORKERS` | no | Compose server process count. Default `4` |

Service-specific variables use a double underscore (`MINIO__*`, `EMAIL__*`).

```env
ENV=LOCAL
DB_URL=postgresql://postgres:postgres@localhost:5432/postgres
SECRET_KEY=change-me-in-production
ROOT_USERNAME=root
ROOT_PASSWORD=Y2hhbmdlLW1l
REDIS_URL=redis://localhost:6379
MINIO__ENDPOINT=localhost:9000
MINIO__ACCESS_KEY=minioadmin
MINIO__SECRET_KEY=minioadmin
MINIO__PUBLIC_BUCKET=public
MINIO__PRIVATE_BUCKET=private
MINIO__SECURE=false
```

`ROOT_PASSWORD` above is the base64 form of `change-me`.

| `ENV` | `DEBUG` | Cache | Swagger | CORS |
|-------|---------|-------|---------|------|
| `LOCAL` | on | dummy | yes | all origins |
| `STAGING` | off | Redis | yes | all origins |
| `PRODUCTION` | off | Redis | hidden | `ALLOWED_ORIGINS` |

`CORS_ALLOW_ALL_ORIGINS` is on when `ENV` is not `PRODUCTION`. In production it is on only when the `ALLOWED_ORIGINS` list is empty.

## Project structure

```text
config/             Settings, ASGI, WSGI, root URLs
user/               User model, user API, root-user bootstrap
identity/           Token, password reset, groups, permissions
attachment/         FileAsset, presigned upload, MinIO cleanup
journal/            LogEntry, log API, file-to-SQLite sync, DB router
notification/       In-app notifications. Mounted at `/api/notifications/`
shared_kernel/      Audit model, audit serializers, health probes
extensions/         Filters, pagination, permissions, validators, DRF mixins
integrations/       MinIO client and templated email
i18n/               Translation msgid overrides for DRF and SimpleJWT
locale/             Django catalogs. Commit .po files. .mo files are compiled
utils/              Loguru setup and cache helpers
env.py              Environment parsing
```

Put a new resource in its own app: `models.py`, `serializers.py`, `viewsets.py`, `urls.py`, and `services.py` when a write is shared with a task. `shared_kernel` holds bases used by every app. It is not where domain models go.

`config/urls.py` includes `shared_kernel`, `journal`, `identity`, and `user`. Health and Swagger are registered in `shared_kernel/urls.py`. There is no auto-discovery of view modules.

## Conventions

- Prefer `ModelViewSet` for full CRUD. Use `AuditableModelViewSet` when the model extends `AuditableModel`. Compose `GenericViewSet` with the mixins you need when the resource is list-only or mostly custom actions. `UserViewSet` is the second case: read, create, update, and `@action` methods, with no destroy.
- Validate input in serializers. Put reusable field checks in `extensions.validators`.
- List serializer fields explicitly, or inherit `ExcludeDeleteModelSerializer` / `ExcludeAuditableModelSerializer` from `shared_kernel.serializers.audit` when the audit columns should stay out of the payload.
- Use `get_serializer_class()` when create, update, and read shapes differ.
- Pass `performed_by=request.user` on auditable writes. The mixins in `shared_kernel.mixins` do this for create, update, and destroy.
- Call `select_related()` and `prefetch_related()` on the viewset queryset when the serializer touches relations.
- Import filters, pagination, permissions, throttling, validators, and DRF mixins from `extensions`. Import `SystemActor` and the audit model from `shared_kernel.models.audit`. Inside an app, use relative imports for that app's modules.
- Keep a simple create or update in the serializer. Move the function into the app's `services.py` when a task or management command must run the same write. `user/services.py` and `attachment/services.py` are the examples. Reads stay on the viewset queryset.

Import order is standard library, third-party, then this project's packages. Ruff enforces that. See [Ruff](#ruff).

## Adding a viewset

1. Add the model in the app. Extend `AuditableModel` when the row needs an actor and soft delete.
2. Add a read serializer and separate create or update serializers when the write body differs from the response.
3. Add a `FilterSet` next to the viewset for typed query filters.
4. Set `queryset`, `permission_classes`, `serializer_class` or `get_serializer_class()`, `filterset_class`, and `pagination_class` on the viewset. There is no global permission default.
5. Register the router in the app's `urls.py` and `include` it from `config/urls.py`.

```python
class ExampleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Example.objects.select_related("owner").all()
    permission_classes = [permissions.DjangoModelPermissions]
    filterset_class = ExampleFilter
    pagination_class = pagination.limit_offset_class(maximum_limit=200)

    def get_serializer_class(self):
        match self.action:
            case "create":
                return ExampleCreateSerializer
            case "update" | "partial_update":
                return ExampleUpdateSerializer
            case _:
                return ExampleSerializer

    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(performed_by=self.request.user)
```

`UserViewSet` is the reference for action-specific serializers, queryset scoping, self-service routes, and the avatar presign flow.

## Choice lists

`ChoiceListModelMixin` swaps in `ChoiceSerializer` when the query string is `?for=options`. `UserViewSet` and `GroupViewSet` include that mixin. The response items are `value`, `label`, and an optional `color`.

For a fixed `TextChoices` enum, add a list action on the owning viewset and serialize the members with `ChoiceLimitOffsetSerializer`. Keep the enum next to the model that stores it. `extensions/models/enums/` holds optional vocabularies such as gender and country. Nothing serves them until an app chooses to.

`TextChoiceField` stores a `TextChoices` member. Pass the enum class as `choices`, not `Enum.choices`.

## Auditable models

`AuditableModel` adds:

- `created_at`, `created_by`
- `updated_at`, `updated_by`
- `is_deleted`, `deleted_at`, `deleted_by`

`objects` hides soft-deleted rows. `all_objects` includes them. `delete(performed_by=...)` sets `is_deleted` and does not remove the row. `QuerySet.delete` and `QuerySet.update` also require `performed_by`.

```python
serializer.save(performed_by=request.user)
instance.delete(performed_by=request.user)
Model.objects.create(..., performed_by=request.user)
```

`save()` stamps `created_by` when it is empty and `updated_by` on later writes, unless the row is being soft-deleted. A custom serializer `create()` or `update()` must pop `performed_by` and pass it into `save()` or `objects.create()`.

| Serializer base | What the client sees |
|-----------------|----------------------|
| `AuditableModelSerializer` | Audit fields, read-only |
| `ExcludeDeleteModelSerializer` | Hides `is_deleted`, `deleted_at`, `deleted_by` |
| `ExcludeAuditableModelSerializer` | Hides the audit fields and the soft-delete fields |

`User` extends `AuditableModel`. `username` is unique only while `is_deleted` is false (`uq_user_username_when_active`), so a soft-deleted login can be registered again. A non-empty email is unique, case-insensitively, on the same condition (`uq_user_email_ci_when_set`). `auth.E003` is silenced because Django's check ignores a unique constraint that has a condition, while `ModelBackend` looks users up through `User.objects`. The user API has no destroy action. A user actor is stored as `str(user.id)`; a system actor is stored as `system:{app}:{action}`.

### System actor

Jobs and `post_migrate` have no request user. Pass a `SystemActor(app, action)` from `shared_kernel.models.audit`. The stored value is `system:{app}:{action}`.

| Call site | Actor |
|-----------|--------|
| `createsuperuser` | `SystemActor("user", "create-superuser")` |
| Root bootstrap | `SystemActor("user", "ensure-root-user")` |
| Password reset | `SystemActor("identity", "reset-password")` |

Do not pass a `SystemActor` to `login()`, a permission check, or a foreign key that expects a saved `User`.

## Permissions, pagination, filtering

`DEFAULT_PERMISSION_CLASSES` is unset, so DRF's `AllowAny` stands. That is deliberate. Health, token, and password-reset views stay public without a special case. Set a class on every view that should not be public.

```python
permission_classes = [permissions.IsAuthenticated]
permission_classes = [permissions.DjangoModelPermissions]
permission_classes = [permissions.permissions_class("auth.view_group")]
```

With stock `DjangoModelPermissions`, safe methods require an authenticated user and do not require a view permission. Unsafe methods map to add, change, and delete. `UserViewSet.get_queryset()` additionally requires `user.view_user` before a list spans every user. Callers without that permission only see themselves. `GroupViewSet` also requires `auth.view_group` on every method, including GET.

`GET /api/permissions/` and the nested group-permission list use `permissions_class("auth.view_group")` and are not paginated.

Default pagination is limit-offset, page size 10, maximum 100 (`extensions.pagination.Max100LimitOffsetPagination`). Override with `pagination.limit_offset_class(maximum_limit=200)` or `pagination_class = None`.

Filter backends, in order:

- `extensions.filters.DjangoFilterBackend` for a `filterset_class`
- `SearchFilter` for `?search=`
- `extensions.filters.OrderingFilter`, which accepts camelCase `?ordering=` and converts it to snake_case field names

Use a `FilterSet` for booleans, dates, and relations. Use `search_fields` for text.

## Authentication

SimpleJWT with rotation and blacklist. Access tokens last 30 days when `DEBUG` is on (`ENV=LOCAL`) and 5 minutes otherwise. Refresh tokens last 7 days. Claims use `tokenType`, `userId`, and `username`.

Send `Authorization: Bearer <access>`.

| Endpoint | Limit |
|----------|--------|
| `POST /api/token/` | 10/minute per username, and 30/minute on the `auth` scope |
| `POST /api/token/refresh/` | 5/minute per user id, and 30/minute on the `reauth` scope |
| Password reset request and confirm | 5/minute |
| `PUT /api/users/me/password/` | 10/minute per user |
| Avatar presign | 10/minute per user |

Throttles use the Django cache. `LOCAL` uses the dummy cache, so those limits are not enforced in local development.

`POST /api/token/` accepts `username` and `password`.

`POST /api/token/refresh/` accepts `refresh`.

`POST /api/token/logout/` accepts `refresh` and blacklists it.

Password reset:

1. `POST /api/password-reset/` with `email`. A well-formed address returns 204. When that address belongs to an active user, a Huey task emails `{FRONTEND_URL}/reset-password?uid=...&token=...`. The token lifetime is `PASSWORD_RESET_TIMEOUT` (24 hours).
2. `POST /api/password-reset/confirm/` with `uid`, `token`, and `newPassword`. On success the password is saved with `SystemActor("identity", "reset-password")` and outstanding refresh tokens for that user are blacklisted.

In `LOCAL` with no `EMAIL__HOST`, the message is printed by the console email backend. The worker must be running for the task to send.

`PUT /api/users/{id}/password/` sets a new password and does not require the current one. `PUT /api/users/me/password/` requires `oldPassword`. Both save the password and blacklist that user's outstanding refresh tokens. An access token already issued stays valid until it expires.

`GET /api/users/me/` returns the signed-in user plus direct and group permissions. `PATCH /api/users/me/` updates that user, including an avatar file id. `update_self` is mapped onto the same action as `retrieve_self`, so both methods share one route.

## Files

`integrations.minio` uploads, downloads, stats, presigns, and deletes objects. Presigned URLs are signed for `MINIO_PUBLIC_URL`, not the internal endpoint.

The avatar flow creates a pending `FileAsset`, returns a presigned PUT, then checks the object on save. Replacing an avatar deletes the previous asset and its object after commit.

| Serializer | Role |
|------------|------|
| `FilePresignedUploadUrlSerializer` | Create a pending `FileAsset` and return a presigned PUT |
| `FileAssetInputSerializer` | Check owner, public flag, and that the MinIO object matches the row |
| `FileAttachmentInputSerializer` | Also reject a file already attached elsewhere |

`UserAvatarUploadUrlSerializer` forces a public image name. `FILE_UPLOAD_MAX_MEMORY_SIZE` is 20 MB. Pending assets older than `FILE_ORPHANED_INTERVAL` (10 minutes) are deleted by `minio_garbage_collect`, which runs daily at 00:00.

An app can publish a readiness check by defining `AppConfig.readiness_checks`. `shared_kernel` checks Postgres and Redis. `attachment` checks MinIO. A check returns `True`, `False`, or `None` when that service is not configured. `None` does not fail `GET /api/health/ready/`.

## Cache

`utils.cache` wraps Django's cache:

- `@cached(base_key, ttl, vary_on_args=True)` stores a function result
- `bump_cache_version(base_key)` invalidates every variant of that key
- Keys bind positional and keyword arguments before hashing

`LOCAL` uses `DummyCache`. Staging and production use Redis at `REDIS_URL`. Huey does not read Redis.

## Background tasks

Huey is `SqlHuey` on the same Postgres database as the app, with its own pooled connection. Results are stored. `immediate` is false, so tasks wait for `python manage.py run_huey`. Compose runs that command as the `worker` service. Worker threads default to `HUEY_WORKERS` (6).

Huey imports each installed app's `tasks` module. These tasks are imported and registered:

| Task | When |
|------|------|
| `identity.tasks.email.send_password_reset_email` | On reset request |
| `journal.tasks.sync.sync_general_logs` | Every 5 minutes |
| `journal.tasks.sync.purge_expired_logs` | Daily at 00:00 |
| `attachment.tasks.minio_garbage_collect` | Daily at 00:00 |
| `identity.tasks.garbage_cleanup.flush_expired_tokens` | Daily at 03:30 |

`shared_kernel.tasks` logs Huey error, locked, canceled, and revoked signals. `identity/tasks/__init__.py` imports the token flush, so Huey registers it with the other identity tasks.

## Operations

### Databases

| Alias | Engine | What it stores |
|-------|--------|----------------|
| `default` | Postgres | Users, files, auth, Huey tables |
| `logs` | SQLite at `logs/logs.sqlite3` | The `journal` app |

`LogDBRouter` sends every `journal` model to `logs` and refuses other apps on that alias. `LogEntry` is the only journal model today. Apply migrations to both aliases. Third-party apps show up in the logs database `django_migrations` table without tables. That is the router skipping them.

The SQLite file is gitignored. Avoid a foreign key from `LogEntry` to a Postgres row.

### Logging

`utils.log` configures Loguru. Request logs are written by `extensions.middlewares.LoggingMiddleware` to `logs/{date}.api.json`. General logs go to `logs/{date}.json`. The journal sync task copies completed lines into `LogEntry`. `GET /api/logs/` requires `from_date` and `to_date` and `IsAdminUser`.

`sys.tracebacklimit` is set to 1 when `utils.log` is imported. Python then keeps only the innermost frame of every traceback in the process, including Django and Huey.

### Internationalization

`LocaleMiddleware` honors `Accept-Language`. Languages are `vi` and `en`. The default is `LANGUAGE_CODE`.

Wrap project strings in `gettext_lazy`. Third-party message ids live under `i18n/` (`drf.py`, `simplejwt.py`) so `makemessages` can see them. Catalogs are in `locale/`. Commit `.po` files. Compile `.mo` locally or in the image:

```bash
python manage.py makemessages -l vi
python manage.py compilemessages
```

The Docker image runs `compilemessages`. On Windows, install gettext with `winget install --id mlocati.GetText -e`.

### Time zone

`TIME_ZONE` is `Asia/Ho_Chi_Minh` and `USE_TZ` is on. Values are stored in UTC. API datetimes are ISO 8601. Use `django.utils.timezone.now` for the current instant. Use `datetime.timedelta` for a fixed duration and `dateutil.relativedelta` for calendar months.

## Ruff

`pyproject.toml` selects Ruff rule `I` (isort) and formats with double quotes, line length 120. First-party packages include `attachment`, `extensions`, `notification`, and `env`.

```bash
pip install ruff
ruff check --fix .
ruff format .
```

Format on save in Cursor: set the Ruff extension as the Python formatter, enable format on save, and set `source.organizeImports` to `explicit`.
