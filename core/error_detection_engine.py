
"""
error_detection_engine.py
CARRERA-HUB v2
Enhanced Error Detection Engine
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List


class ErrorSeverity(Enum):
    INFO=auto()
    WARNING=auto()
    CRITICAL=auto()


@dataclass
class ErrorEvent:
    package:str
    code:str
    message:str
    severity:ErrorSeverity
    timestamp:float=field(default_factory=time.time)


class ErrorDetectionEngine:
    """
    Detect Roblox runtime errors independently per package.

    Detects supported Roblox errors and notifies
    RecoveryScheduler without performing recovery.
    """

    DEFAULT_PATTERNS={
        "264":re.compile(r"264"),
        "267":re.compile(r"267"),
        "268":re.compile(r"268"),
        "277":re.compile(r"277"),
        "279":re.compile(r"279"),
    }

    def __init__(
        self,
        config_manager,
        state_manager,
        android_service,
        logger,
        recovery_scheduler=None,
    ):
        self.config=config_manager
        self.state=state_manager
        self.android=android_service
        self.logger=logger
        self.scheduler=recovery_scheduler

        self._lock=threading.RLock()
        self._patterns=dict(self.DEFAULT_PATTERNS)
        self._listeners:List[Callable]=[]
        self._history:Dict[str,List[ErrorEvent]]={}

    def subscribe(self,callback:Callable):
        self._listeners.append(callback)

    def register_error(self,code:str,pattern:str):
        self._patterns[code]=re.compile(pattern,re.I)

    def _emit(self,event:ErrorEvent):
        for cb in list(self._listeners):
            try:
                cb(event)
            except Exception:
                pass

    def _record(self,event:ErrorEvent):
        self._history.setdefault(event.package,[]).append(event)

    def _scan_logcat(self,package:str):
        try:
            result=self.android.logcat.read(package)
            if not result.success:
                return None
            return result.stdout
        except Exception:
            return None

    def scan_package(self,package:str):
        text=self._scan_logcat(package)
        if not text:
            return []

        detected=[]

        for code,regex in self._patterns.items():
            if not regex.search(text):
                continue

            event=ErrorEvent(
                package=package,
                code=code,
                message=f"Roblox Error {code}",
                severity=ErrorSeverity.CRITICAL
            )

            self._record(event)

            try:
                self.state.set_error(package,code)
            except Exception:
                pass

            if self.scheduler:
                self.scheduler.request(
                    package,
                    reason=f"error_{code}"
                )

            try:
                self.logger.warning(
                    f"[ERROR] {package} Error {code}"
                )
            except Exception:
                pass

            self._emit(event)
            detected.append(event)

        return detected

    def scan_all(self,registry):
        events=[]
        with self._lock:
            for profile in registry.enabled():
                events.extend(
                    self.scan_package(profile.package_name)
                )
        return events

    def history(self,package:str):
        return list(self._history.get(package,[]))
        
