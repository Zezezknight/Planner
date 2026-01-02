import json
import logging.handlers
import logging
import contextvars
from datetime import datetime, timezone
import queue
from src.app.core.config import settings
import traceback
import re


request_id_var = contextvars.ContextVar("request_id_var", default="system")
user_id_var = contextvars.ContextVar("user_id_var", default="system")


class SensitiveDataFilter(logging.Filter):
    # Filters sensitive data
    def filter(self, record):
        patterns = [
            (r'(password)\s*[=:]\s*([^\s,&]+)', r'\1= ******'),
            (r'(token)\s*:\s*([^\s,&]+)', r'\1: ******'),
            (r'(api_key)\s*:\s*([^\s,&]+)', r'\1: ******')
        ]
        for pattern, replacement in patterns:
            record.msg = re.sub(pattern, replacement, record.msg, flags=re.IGNORECASE)
        return True


class ContextCatchFilter(logging.Filter):
    # Catches context like request_id, user_id and exc_info
    def filter(self, record):
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        if record.exc_info:
            exc_type, exc_msg, exc_stack = record.exc_info
            record.error = exc_type.__name__
            record.stack = "".join(traceback.format_exception(exc_type, exc_msg, exc_stack))
        return True


class JSONFormatter(logging.Formatter):
    # Formats record into JSON
    def format(self, record) -> str:
        extra_data = {
            "method": getattr(record, "http_method", None),
            "path": getattr(record, "http_path", None),
            "status": getattr(record, "http_status", None),
            "duration_ms": getattr(record, "http_duration_ms", None),
            "error": getattr(record, "error", None),
            "stack": getattr(record, "stack", None)
        }

        log_entry = {
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.msg.split("\n")[0],
            "request_id": record.request_id if hasattr(record, "request_id") else request_id_var.get(),
            "user_id": record.user_id if hasattr(record, "user_id") else user_id_var.get()
        }

        for field in ["method", "path", "status", "duration_ms", "error", "stack"]:
            value = extra_data[field]
            if value:
                log_entry[field] = value
        return json.dumps(log_entry, ensure_ascii=False)


def init_logging():
    # Starts queue_listener
    log_queue = queue.Queue()
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_handler.addFilter(ContextCatchFilter())
    queue_handler.addFilter(SensitiveDataFilter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())

    rotating_file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE_PATH,
        maxBytes=settings.LOG_ROTATE_MB*1024*1024,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    rotating_file_handler.setFormatter(JSONFormatter())

    queue_listener = logging.handlers.QueueListener(
        log_queue,
        console_handler,
        rotating_file_handler
    )
    queue_listener.start()

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.handlers.clear()
    root_logger.addHandler(queue_handler)

    logging._queue_listener = queue_listener


def stop_logging():
    # Stops queue_listener
    listener = getattr(logging, "_queue_listener")
    listener.stop()