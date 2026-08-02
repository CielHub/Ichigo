"""
logger.py
CARRERA-HUB v2
Phase 3.1 Foundation Logger
"""

from __future__ import annotations

import logging
import logging.handlers
import threading
from pathlib import Path
from datetime import datetime


class LoggerManager:
    """
    Central logger for all modules.

    Supports:
    - Console logging
    - Rotating file logging
    - Runtime log level
    - Thread safety
    """

    def __init__(
        self,
        name: str = "CARRERA-HUB",
        log_dir: str = "logs",
        level: str = "INFO",
        console: bool = True,
        file: bool = True,
    ):
        self._lock = threading.RLock()
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self._logger.propagate = False

        if self._logger.handlers:
            return

        Path(log_dir).mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )

        if console:
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self._logger.addHandler(ch)

        if file:
            fh = logging.handlers.RotatingFileHandler(
                Path(log_dir) / "carrera.log",
                maxBytes=2 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)

    def debug(self, msg: str):
        with self._lock:
            self._logger.debug(msg)

    def info(self, msg: str):
        with self._lock:
            self._logger.info(msg)

    def warning(self, msg: str):
        with self._lock:
            self._logger.warning(msg)

    def error(self, msg: str):
        with self._lock:
            self._logger.error(msg)

    def critical(self, msg: str):
        with self._lock:
            self._logger.critical(msg)

    def exception(self, msg: str):
        with self._lock:
            self._logger.exception(msg)

    def runtime_event(self, package: str, event: str, detail: str = ""):
        self.info(f"[{package}] {event} {detail}".strip())

    def recovery_event(self, package: str, result: str):
        self.info(f"[RECOVERY] [{package}] {result}")

    def launch_event(self, package: str):
        self.info(f"[LAUNCH] {package}")

    def detector_event(self, package: str, error_code: int):
        self.warning(f"[DETECTOR] {package} Error {error_code}")

    def set_level(self, level: str):
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    def get_logger(self):
        return self._logger

    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
