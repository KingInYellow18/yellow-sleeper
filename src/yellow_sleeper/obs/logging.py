from __future__ import annotations

import json
import logging
import logging.handlers
import re
from pathlib import Path
from typing import Any

REDACT_KEYS = re.compile(r"league_id|user_id|username", re.IGNORECASE)


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            record.extra_data = _redact(record.extra_data)
        return True


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            payload["extra"] = record.extra_data
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(cache_dir: Path) -> None:
    log_path = cache_dir / "logs" / "server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.TimedRotatingFileHandler(
        log_path,
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RedactionFilter())

    root = logging.getLogger("yellow_sleeper")
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)
    root.propagate = False


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***REDACTED***" if REDACT_KEYS.search(str(key)) else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value
