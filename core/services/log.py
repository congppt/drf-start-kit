import json
from contextlib import suppress
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from utils.log import LOG_DIR

LOG_PATH = Path(LOG_DIR)
LOG_FILE_DATE_FORMAT = "%y-%m-%d"
STREAM_SUFFIX = {
    "api": ".api.json",
    "api_unsafe": ".api.unsafe.json",
    "general": ".json",
    "error": ".error.json",
    "background": ".background.json",
}
LOG_STREAMS = list(STREAM_SUFFIX.keys())
DEFAULT_STREAM = "api_unsafe"

def _iter_dates(from_date: date, to_date: date) -> list[str]:
    return [
        (from_date + timedelta(days=i)).strftime(LOG_FILE_DATE_FORMAT) for i in range((to_date - from_date).days + 1)
    ]


def _matches_min_level(record: dict, min_level: int | None) -> bool:
    if min_level is None:
        return True
    with suppress(KeyError):
        return record["level"]["no"] >= min_level
    return False


def _coerce_query_value(actual: Any, query_value: str) -> Any:
    if isinstance(actual, bool):
        return query_value.lower() in {"1", "true", "yes"}
    if isinstance(actual, int):
        return int(query_value)
    if isinstance(actual, float):
        return float(query_value)
    if isinstance(actual, str):
        return query_value
    if isinstance(actual, dict | list):
        return json.loads(query_value)
    return query_value


def _extra_values_equal(actual: Any, query_value: str) -> bool:
    if actual == query_value:
        return True
    if type(actual) is type(query_value):
        return False
    try:
        return actual == _coerce_query_value(actual, query_value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return False


def _matches_extra(record: dict, extra_filters: dict[str, str]) -> bool:
    extra = record.get("extra") or {}

    for key, query_value in extra_filters.items():
        if key not in extra:
            return False
        if not _extra_values_equal(extra[key], query_value):
            return False
    return True


def _matches_search(entry: dict, search: str | None) -> bool:
    if not search:
        return True
    record = entry.get("record", {})
    haystack = f"{entry.get('text', '')} {record.get('message', '')}".lower()
    return search.lower() in haystack


def list_log_files() -> list[dict]:
    files = []
    if not LOG_PATH.is_dir():
        return files

    for path in sorted(LOG_PATH.glob("*.json"), reverse=True):
        name = path.name
        if name.endswith(".error.json"):
            stream, date_stem = "error", name.removesuffix(".error.json")
        elif name.endswith(".background.json"):
            stream, date_stem = "background", name.removesuffix(".background.json")
        elif name.endswith(".api.unsafe.json"):
            stream, date_stem = "api_unsafe", name.removesuffix(".api.unsafe.json")
        elif name.endswith(".api.json"):
            stream, date_stem = "api", name.removesuffix(".api.json")
        else:
            stream, date_stem = "general", name.removesuffix(".json")
        try:
            file_date = datetime.strptime(date_stem, LOG_FILE_DATE_FORMAT).date()
        except ValueError:
            continue
        files.append({"date": file_date.isoformat() if file_date else None, "stream": stream, "size": path.stat().st_size})
    return files


def query_logs(
    *,
    from_date: date,
    to_date: date,
    stream: str,
    min_level: int | None = None,
    search: str | None = None,
    extra_filters: dict[str, str] | None = None,
) -> list[dict]:
    matched = []
    for date_stem in _iter_dates(from_date, to_date):
        log_path = LOG_PATH / f"{date_stem}{STREAM_SUFFIX[stream]}"
        if not log_path.is_file():
            continue
        with log_path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                record = entry.get("record", {})
                if not _matches_min_level(record, min_level):
                    continue
                if not _matches_extra(record, extra_filters or {}):
                    continue
                if not _matches_search(entry, search):
                    continue
                matched.append(entry["record"])

    matched.sort(key=lambda item: item["time"]["timestamp"], reverse=True)
    return matched
