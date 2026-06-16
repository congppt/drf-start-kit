import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

__ENV = os.getenv("ENV", "LOCAL").upper()
IS_PRODUCTION = __ENV == "PRODUCTION"
IS_LOCAL = not IS_PRODUCTION

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise EnvironmentError("DB_URL is not configured")
__parsed_db_url = urlparse(DB_URL)
DB_HOST = __parsed_db_url.hostname
DB_PORT = __parsed_db_url.port
DB_USER = __parsed_db_url.username
DB_PASSWORD = __parsed_db_url.password
DB_NAME = __parsed_db_url.path.lstrip("/")

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL and not IS_LOCAL:
    raise EnvironmentError("REDIS_URL is not configured")

MINIO_ENDPOINT = os.getenv("MINIO__ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO__ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO__SECRET_KEY")
MINIO_PUBLIC_BUCKET = os.getenv("MINIO__PUBLIC_BUCKET")
MINIO_PRIVATE_BUCKET = os.getenv("MINIO__PRIVATE_BUCKET")
MINIO_PUBLIC_URL = os.getenv("MINIO__PUBLIC_URL", f"http://{MINIO_ENDPOINT}")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise EnvironmentError("SECRET_KEY is not configured")

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "vi")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",") if not IS_LOCAL else []
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if not IS_LOCAL else []

HUEY_WORKERS = int(os.getenv("HUEY_WORKERS", "6"))
if HUEY_WORKERS < 1:
    raise EnvironmentError("HUEY_WORKERS must be at least 1")