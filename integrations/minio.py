import mimetypes
from datetime import timedelta
from typing import Iterable
from urllib.parse import quote, urlparse
from uuid import UUID

import certifi
import env
import urllib3
from django.core.files import File

from minio import Minio, S3Error
from minio.deleteobjects import DeleteObject


class MinioClient:
    def __init__(self):
        self.__client: Minio | None = None
        self.__presign_client: Minio | None = None

    def __build_client(self, *, endpoint: str, secure: bool) -> Minio:
        connect_timeout = timedelta(seconds=10).seconds
        read_timeout = timedelta(minutes=5).seconds
        http_client = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=connect_timeout, read=read_timeout),
            maxsize=10,
            cert_reqs="CERT_REQUIRED",
            ca_certs=getattr(env, "SSL_CERT_FILE", certifi.where()),
            retries=urllib3.Retry(total=5, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504]),
        )
        return Minio(
            endpoint=endpoint,
            access_key=self.__get_config("MINIO_ACCESS_KEY"),
            secret_key=self.__get_config("MINIO_SECRET_KEY"),
            http_client=http_client,
            secure=secure,
        )

    @property
    def client(self) -> Minio:
        """Internal client for upload/download/stat/delete against MINIO_ENDPOINT."""
        if self.__client is None:
            self.__client = self.__build_client(
                endpoint=self.__get_config("MINIO_ENDPOINT"),
                secure=env.MINIO_SECURE,
            )
        return self.__client

    @property
    def presign_client(self) -> Minio:
        """
        Public-facing client used only to mint URLs browsers can open.

        Endpoint/secure are taken from MINIO_PUBLIC_URL so signatures match the
        host clients actually call (which may differ from the internal endpoint).
        """
        if self.__presign_client is None:
            endpoint, secure = self.__get_public_endpoint()
            self.__presign_client = self.__build_client(endpoint=endpoint, secure=secure)
        return self.__presign_client

    def __get_config(self, name: str) -> str:
        resolved = getattr(env, name, None)
        if not resolved:
            raise EnvironmentError(f"{name} is not configured")
        return resolved

    def __get_bucket(self, is_public: bool) -> str:
        if is_public:
            return self.__get_config("MINIO_PUBLIC_BUCKET")
        return self.__get_config("MINIO_PRIVATE_BUCKET")

    def __get_public_url(self) -> str:
        return self.__get_config("MINIO_PUBLIC_URL").rstrip("/")

    def __get_public_endpoint(self) -> tuple[str, bool]:
        parsed = urlparse(self.__get_public_url())
        if not parsed.netloc:
            raise EnvironmentError("MINIO_PUBLIC_URL must include a host, e.g. http://localhost:9000")
        return parsed.netloc, parsed.scheme == "https"

    def __get_content_type(self, name: str) -> str:
        content_type, _ = mimetypes.guess_type(name)
        return content_type or "application/octet-stream"

    def get_public_url(self, object_uid: UUID) -> str:
        return f"{self.__get_public_url()}/{self.__get_bucket(is_public=True)}/{str(object_uid)}"

    def upload(self, file: File, object_uid: UUID, is_public: bool = False):
        metadata = self.client.put_object(
            bucket_name=self.__get_bucket(is_public),
            object_name=str(object_uid),
            data=file.file,
            length=file.size,
            content_type=self.__get_content_type(file.name),
        )
        return metadata

    def download(self, object_uid: UUID, is_public: bool = False):
        return self.client.get_object(self.__get_bucket(is_public), str(object_uid))

    def stat(self, object_uid: UUID, is_public: bool = False):
        try:
            return self.client.stat_object(self.__get_bucket(is_public), str(object_uid))
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            raise e

    def presigned_upload(
        self,
        object_uid: UUID,
        expires: timedelta,
        is_public: bool = False,
    ) -> str:
        return self.presign_client.presigned_put_object(
            bucket_name=self.__get_bucket(is_public),
            object_name=str(object_uid),
            expires=expires,
        )

    def presigned_download(
        self,
        object_uid: UUID,
        name: str,
        expires: timedelta = timedelta(minutes=10),
    ) -> str:
        quoted_name = quote(name)
        return self.presign_client.presigned_get_object(
            bucket_name=self.__get_bucket(is_public=False),
            object_name=str(object_uid),
            expires=expires,
            response_headers={
                "response-content-type": self.__get_content_type(name),
                "response-content-disposition": (f"attachment; filename*=UTF-8''{quoted_name}"),
            },
        )

    def delete(self, object_uids: Iterable[UUID], is_public: bool = False):
        objects = [DeleteObject(str(object_uid)) for object_uid in object_uids]
        if not objects:
            return []
        errors = self.client.remove_objects(self.__get_bucket(is_public), objects)
        return list(errors)


minio = MinioClient()
