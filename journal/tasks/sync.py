import json
from contextlib import suppress
from datetime import date, datetime
from pathlib import Path

import env
from django.utils import timezone
from huey import crontab
from huey.contrib import djhuey

from utils.log import LOG_DIR, logger

from .. import models, serializers

LOG_PATH = Path(LOG_DIR)
LOG_FILE_DATE_FORMAT = "%y-%m-%d"
SYNC_STATE_FILE = LOG_PATH / ".log-sync-state.json"
BULK_INSERT_BATCH_SIZE = 500


def _log_file_for_date(value: date) -> Path:
    return LOG_PATH / f"{value.strftime(LOG_FILE_DATE_FORMAT)}.json"


def _today_log_file() -> Path:
    return _log_file_for_date(timezone.localdate())


def _file_date(path: Path) -> date | None:
    with suppress(ValueError):
        return datetime.strptime(path.stem, LOG_FILE_DATE_FORMAT).date()
    return None


def _load_sync_state() -> dict:
    if not SYNC_STATE_FILE.is_file():
        return {}
    with suppress(OSError, json.JSONDecodeError):
        return json.loads(SYNC_STATE_FILE.read_text(encoding="utf-8"))
    return {}


def _save_sync_state(*, file_name: str, offset: int) -> None:
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    SYNC_STATE_FILE.write_text(json.dumps({"file": file_name, "offset": offset}), encoding="utf-8")


def _resolve_sync_target(state: dict) -> tuple[Path, int]:
    today = _today_log_file()
    file_name = state.get("file")
    offset = int(state.get("offset") or 0)

    if not file_name:
        return today, 0

    current = LOG_PATH / file_name
    if not current.is_file():
        return today, 0

    current_date = _file_date(current)
    if current_date and current_date < timezone.localdate():
        if offset >= current.stat().st_size:
            return today, 0
        return current, offset

    return current, offset


def _log_line_to_entry(line: dict) -> models.LogEntry | None:
    with suppress(Exception):
        record = line["record"]
        extra = record["extra"]
        log_id = extra.pop("id")
        data = {
            "id": log_id,
            "timestamp": record["time"]["repr"],
            "level": record["level"]["no"],
            "message": record["message"],
            "extra": extra,
        }
        serializer = serializers.LogEntrySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()
    return None


def _read_log_entries(path: Path, start_offset: int) -> tuple[list[models.LogEntry], int]:
    entries: list[models.LogEntry] = []
    if not path.is_file():
        return entries, start_offset

    offset = start_offset
    with path.open("rb") as handle:
        handle.seek(start_offset)
        while True:
            line_start = handle.tell()
            line = handle.readline()
            if not line:
                break
            if not line.endswith(b"\n"):
                offset = line_start
                break
            offset = handle.tell()
            line_text = line.decode("utf-8").strip()
            if not line_text:
                continue
            with suppress(json.JSONDecodeError):
                log_entry = _log_line_to_entry(json.loads(line_text))
                if log_entry is not None:
                    entries.append(log_entry)
    return entries, offset


@djhuey.db_periodic_task(crontab(minute="*/5"))
@djhuey.lock_task("sync-general-logs")
def sync_general_logs():
    logger.info("Starting general log sync")
    state = _load_sync_state()
    log_file, start_offset = _resolve_sync_target(state)

    if not log_file.is_file():
        logger.info("General log sync skipped", extra={"reason": "log file not found", "file": log_file.name})
        return 0

    entries, end_offset = _read_log_entries(log_file, start_offset)
    inserted = 0
    for batch_offset in range(0, len(entries), BULK_INSERT_BATCH_SIZE):
        batch = entries[batch_offset : batch_offset + BULK_INSERT_BATCH_SIZE]
        created = models.LogEntry.objects.bulk_create(batch, ignore_conflicts=True)
        inserted += len(created)

    _save_sync_state(file_name=log_file.name, offset=end_offset)
    logger.info(
        "General log sync completed",
        extra={"inserted_count": inserted, "file": log_file.name, "offset": end_offset},
    )
    return inserted


@djhuey.db_periodic_task(crontab(minute="0", hour="0"))
@djhuey.lock_task("purge-expired-logs")
def purge_expired_logs():
    logger.info("Starting expired log purge")
    cutoff = timezone.now() - timezone.timedelta(days=env.LOG_RETENTION)
    deleted_count, _ = models.LogEntry.objects.filter(timestamp__lt=cutoff).delete()
    logger.info("Expired log purge completed", extra={"deleted_count": deleted_count})
    return deleted_count
