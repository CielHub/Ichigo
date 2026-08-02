"""
error_detection_engine.py
CARRERA-HUB v2
Phase 3.3 - Error Detection Engine
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional


class ErrorSeverity(Enum):
    INFO = auto()
    WARNING = auto()
    CRITICAL = auto()


@dataclass
class ErrorEvent:
    package: str
    error_code: int
    severity: ErrorSeverity
    source: str
    message: str
    timestamp: float


class ErrorDetectionEngine:
    """
    Detect Roblox runtime errors.

    Responsibilities:
    - Parse log source
    - Detect supported error codes
    - Update StateManager
    - Emit error events

    Does NOT:
    - Launch
    - Recover
    - Kill process
    """

    DEFAULT_CODES = {
        264: ErrorSeverity.WARNING,
        267: ErrorSeverity.CRITICAL,
        268: ErrorSeverity.CRITICAL,
        277: ErrorSeverity.CRITICAL,
        279: ErrorSeverity.WARNING,
    }

    def __init__(self, config_manager,
                 state_manager,
                 android_service,
                 logger):
        self.config = config_manager
        self.state = state_manager
        self.android = android_service
        self.logger = logger

        self._lock = threading.RLock()
        self._callbacks: List[Callable] = []
        self._registry = dict(self.DEFAULT_CODES)

    def subscribe(self, callback: Callable):
        self._callbacks.append(callback)

    def register_error(self, code: int,
                       severity: ErrorSeverity = ErrorSeverity.WARNING):
        self._registry[code] = severity

    def _emit(self, event: ErrorEvent):
        for cb in list(self._callbacks):
            try:
                cb(event)
            except Exception:
                pass

    def scan_package(self, package_name: str) -> List[ErrorEvent]:
        events: List[ErrorEvent] = []

        try:
            result = self.android.logcat.dump()
            if not result.success:
                return events

            for line in result.stdout.splitlines():
                if package_name not in line:
                    continue

                match = re.search(r"(?:Error|error)\s*(\d{3})", line)
                if not match:
                    continue

                code = int(match.group(1))
                if code not in self._registry:
                    continue

                event = ErrorEvent(
                    package=package_name,
                    error_code=code,
                    severity=self._registry[code],
                    source="logcat",
                    message=line.strip(),
                    timestamp=time.time(),
                )

                try:
                    self.state.record_crash(package_name, code)
                except Exception:
                    pass

                try:
                    self.logger.detector_event(package_name, code)
                except Exception:
                    pass

                self._emit(event)
                events.append(event)

        except Exception:
            pass

        return events

    def scan_all(self, package_names: List[str]) -> Dict[str, List[ErrorEvent]]:
        return {pkg: self.scan_package(pkg) for pkg in package_names}
