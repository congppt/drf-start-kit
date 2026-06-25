import contextlib
import json
import os
import time
import uuid
from typing import Any
from urllib.parse import parse_qs

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken

from utils.log import LOG_DIR, LOG_OPTS, LogLevel, logger

API_LOG_NAME = __name__


def _is_api_log(record):
    return record["name"] == API_LOG_NAME


logger.add(
    os.path.join(LOG_DIR, "{time:YY-MM-DD}.api.json"),
    level=LogLevel.INFO,
    filter=_is_api_log,
    **LOG_OPTS,
)


class LoggingMiddleware:
    async_capable = True
    sync_capable = False

    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    def __get_client_ip(self, request):
        ip_addresses = request.headers.get("x-forwarded-for")
        if ip_addresses:
            return ip_addresses.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def __extract_request_info(self, request):
        extra = {
            "id": request.headers.get("x-request-id") or str(uuid.uuid4()),
            "ip_address": self.__get_client_ip(request),
            "path": request.path,
            "query_params": request.GET.dict(),
            "method": request.method,
            "protocol": request.scheme,
            "protocol_version": request.META.get("SERVER_PROTOCOL"),
            "content_type": request.headers.get("content-type"),
        }
        content_type = extra["content_type"]
        if request.method not in ["GET", "HEAD", "OPTIONS"] and content_type:
            body = request.body
            parsed_body = "[binary]"
            # Parse body based on content type
            try:
                if "application" in content_type or "text" in content_type:
                    parsed_body = body.decode("utf-8")
                elif "multipart" in content_type:
                    parsed_body = "[multipart form data]"
                if "json" in content_type:
                    parsed_body = json.loads(parsed_body)
                elif "x-www-form-urlencoded" in content_type:
                    parsed_body = parse_qs(parsed_body)
                    # Convert lists of single values to single values
                    parsed_body = {k: v[0] if len(v) == 1 else v for k, v in parsed_body.items()}
            except (UnicodeDecodeError, json.JSONDecodeError):
                parsed_body = "[Failed to parse request body]"

            def filter_sensitive_data(data: Any):
                if isinstance(data, dict):
                    return {
                        k: "[censored]"
                        if "password" in str(k).lower() and isinstance(v, str | list)
                        else filter_sensitive_data(v)
                        for k, v in data.items()
                    }
                elif isinstance(data, list):
                    return [filter_sensitive_data(item) for item in data]
                return data

            extra["body"] = filter_sensitive_data(parsed_body)
        return extra

    def __resolve_username(self, request):
        username = None
        with contextlib.suppress(Exception):
            username = request.user.username
        if not username and (auth_header := request.headers.get("authorization")):
            __, raw_token = auth_header.split(" ")
            with contextlib.suppress(Exception):
                token = AccessToken(raw_token)
                username = token[settings.SIMPLE_JWT["USERNAME_CLAIM"]]
        return username

    async def __call__(self, request):
        start = time.perf_counter()
        extra = self.__extract_request_info(request)
        response = await self.get_response(request)
        process_duration = time.perf_counter() - start
        extra["duration"] = process_duration
        extra["status_code"] = response.status_code
        extra["username"] = self.__resolve_username(request)
        response.headers["X-Request-ID"] = extra["id"]
        logger.info("", **extra)
        return response

    def process_exception(self, request, exception):
        extra = self.__extract_request_info(request)
        logger.opt(exception=exception).exception(str(exception), **extra)
        return None
