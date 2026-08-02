"""
watchdog_engine.py
CARRERA-HUB v2
Phase 3.5 - Watchdog Engine
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional


class WatchdogStatus(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


class HealthLevel(Enum):
    HEALTHY = auto()
    WARNING = auto()
    CRITICAL = auto()


@dataclass
class EngineHeartbeat:
    name: str
    last_seen: float = field(default_factory=time.time)
    timeout: float = 30.0
    health: HealthLevel = HealthLevel.HEALTHY
    enabled: bool = True


@dataclass
class WatchdogEvent:
    engine: str
    health: HealthLevel
    message: str
    timestamp: float = field(default_factory=time.time)


class WatchdogEngine:
    """
    Supervises internal engines.

    Responsibilities:
    - Track engine heartbeats
    - Detect stalled engines
    - Emit watchdog events

    Does NOT restart engines directly.
    """

    def __init__(self, config_manager, state_manager, logger):
        self.config = config_manager
        self.state = state_manager
        self.logger = logger

        self._lock = threading.RLock()
        self._status = WatchdogStatus.STOPPED
        self._engines: Dict[str, EngineHeartbeat] = {}
        self._callbacks: List[Callable] = []

    def register_engine(self, name: str, timeout: float = 30.0):
        with self._lock:
            self._engines[name] = EngineHeartbeat(name=name, timeout=timeout)

    def heartbeat(self, name: str):
        hb = self._engines.get(name)
        if hb:
            hb.last_seen = time.time()
            hb.health = HealthLevel.HEALTHY

    def subscribe(self, callback: Callable):
        self._callbacks.append(callback)

    def _emit(self, event: WatchdogEvent):
        for cb in list(self._callbacks):
            try:
                cb(event)
            except Exception:
                pass

    def start(self):
        self._status = WatchdogStatus.RUNNING

    def stop(self):
        self._status = WatchdogStatus.STOPPED

    def scan(self):
        now = time.time()
        events = []

        with self._lock:
            for hb in self._engines.values():
                if not hb.enabled:
                    continue

                elapsed = now - hb.last_seen
                if elapsed <= hb.timeout:
                    continue

                hb.health = HealthLevel.CRITICAL
                event = WatchdogEvent(
                    engine=hb.name,
                    health=hb.health,
                    message=f"Heartbeat timeout ({elapsed:.1f}s)"
                )

                try:
                    self.logger.warning(
                        f"[WATCHDOG] {hb.name} timeout ({elapsed:.1f}s)"
                    )
                except Exception:
                    pass

                self._emit(event)
                events.append(event)

        return events

    def snapshot(self):
        return {
            "status": self._status.name,
            "engines": {
                name: {
                    "last_seen": hb.last_seen,
                    "timeout": hb.timeout,
                    "health": hb.health.name,
                    "enabled": hb.enabled,
                }
                for name, hb in self._engines.items()
            }
        }
