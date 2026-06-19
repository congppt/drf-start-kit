import os
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

load_dotenv()

__ENV = os.getenv("ENV", "LOCAL").upper()
_VALID_ENVS = frozenset({"LOCAL", "STAGING", "PRODUCTION"})
if __ENV not in _VALID_ENVS:
    raise EnvironmentError(f"ENV must be one of {sorted(_VALID_ENVS)}, got {__ENV!r}")

IS_LOCAL = __ENV == "LOCAL"
IS_STAGING = __ENV == "STAGING"
IS_PRODUCTION = __ENV == "PRODUCTION"


def _db_url_options(query: str) -> dict[str, str]:
    if not query:
        return {}
    return {key: values[0] for key, values in parse_qs(query).items() if values}


DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise EnvironmentError("DB_URL is not configured")
__parsed_db_url = urlparse(DB_URL)
DB_HOST = __parsed_db_url.hostname
DB_PORT = __parsed_db_url.port
DB_USER = __parsed_db_url.username
DB_PASSWORD = __parsed_db_url.password
DB_NAME = __parsed_db_url.path.lstrip("/")
DB_OPTIONS = _db_url_options(__parsed_db_url.query)

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL and not IS_LOCAL:
    raise EnvironmentError("REDIS_URL is not configured")

MINIO_ENDPOINT = os.getenv("MINIO__ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO__ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO__SECRET_KEY")
MINIO_PUBLIC_BUCKET = os.getenv("MINIO__PUBLIC_BUCKET")
MINIO_PRIVATE_BUCKET = os.getenv("MINIO__PRIVATE_BUCKET")
MINIO_SECURE = os.getenv("MINIO__SECURE", "false").lower() in {"1", "true", "yes"}
_default_minio_scheme = "https" if MINIO_SECURE else "http"
MINIO_PUBLIC_URL = os.getenv("MINIO__PUBLIC_URL", f"{_default_minio_scheme}://{MINIO_ENDPOINT}")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise EnvironmentError("SECRET_KEY is not configured")

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "vi")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",") if not IS_LOCAL else []
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if not IS_LOCAL else []

HUEY_WORKERS = int(os.getenv("HUEY_WORKERS", "6"))
if HUEY_WORKERS < 1:
    raise EnvironmentError("HUEY_WORKERS must be at least 1")

# Per Gunicorn process (sync worker ≈ one concurrent request). Safety overhead
DB_POOL_MIN_SIZE = 1
DB_POOL_MAX_SIZE = 4

LOG_RETENTION = int(os.getenv("LOG_RETENTION", "60"))
