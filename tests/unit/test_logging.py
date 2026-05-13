from __future__ import annotations

import json
import logging
from pathlib import Path

from yellow_sleeper.obs.logging import configure_logging


def test_logging_writes_json_and_redacts_sensitive_extra(tmp_path: Path) -> None:
    configure_logging(tmp_path)
    logger = logging.getLogger("yellow_sleeper.test")

    logger.info(
        "tool invocation",
        extra={
            "extra_data": {
                "league_id": "1234567890",
                "nested": {"username": "brad"},
                "ok": "visible",
            }
        },
    )

    for handler in logging.getLogger("yellow_sleeper").handlers:
        handler.flush()

    log_path = tmp_path / "logs" / "server.log"
    payload = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])

    assert payload["msg"] == "tool invocation"
    assert payload["extra"]["league_id"] == "***REDACTED***"
    assert payload["extra"]["nested"]["username"] == "***REDACTED***"
    assert payload["extra"]["ok"] == "visible"
    assert "1234567890" not in log_path.read_text(encoding="utf-8")
    assert "brad" not in log_path.read_text(encoding="utf-8")
