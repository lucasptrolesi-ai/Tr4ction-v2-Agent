# backend/core/logging_config.py

import logging
import json
import sys
import os
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_record.update(record.extra)

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging(level: int = None) -> None:
    """
    Setup structured logging for the application.
    
    Args:
        level: Optional log level. If not provided, reads from LOG_LEVEL env var.
               Defaults to INFO if neither is set.
    """
    # Get log level from env if not provided
    if level is None:
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, log_level_str, logging.INFO)
    
    root = logging.getLogger()
    root.setLevel(level)

    # limpa handlers antigos
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # reduz ruído do uvicorn / fastapi
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Log the configured level
    root.info(f"Logging configured at level: {logging.getLevelName(level)}")
