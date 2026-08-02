
"""
watchdog_engine.py
CARRERA-HUB v2
Enhanced Watchdog Engine
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List


class HealthState(Enum):
    HEALTHY=auto()
    WARNING=auto()
    CRITICAL=auto()
    UNKNOWN=auto()


@dataclass
class WatchTarget:
    name:str
    heartbeat:Callable[[],float]
    restart_callback:Callable|None=None
    timeout:float=30.0
    state:HealthState=HealthState.UNKNOWN
    last_seen:float=0.0
    failures:int=0
    checks:int=0
    last_reason:str=""


class WatchdogEngine:
    """
    Runtime supervisor.

    Monitors engines by heartbeat only.
    Does not implement business logic or recovery itself.
    """

    def __init__(self, config, state, logger):
        self.config=config
        self.state=state
        self.logger=logger
        self._targets:Dict[str,WatchTarget]={}
        self._listeners:List[Callable]=[]
        self._lock=threading.RLock()

    def register(self,name,heartbeat,restart_callback=None,timeout=None):
        self._targets[name]=WatchTarget(
            name=name,
            heartbeat=heartbeat,
            restart_callback=restart_callback,
            timeout=timeout or self.config.get(
                "watchdog","timeout",default=30
            )
        )

    def subscribe(self,callback):
        self._listeners.append(callback)

    def _emit(self,event,target):
        for cb in list(self._listeners):
            try:
                cb(event,target)
            except Exception:
                pass

    def scan(self):
        now=time.time()

        with self._lock:
            for target in self._targets.values():
                target.checks += 1

                try:
                    target.last_seen = float(target.heartbeat())
                except Exception:
                    target.last_seen = 0

                age = now - target.last_seen if target.last_seen else 999999

                if age <= target.timeout:
                    target.state = HealthState.HEALTHY
                    continue

                if age <= target.timeout * 2:
                    target.state = HealthState.WARNING
                    target.last_reason = "heartbeat timeout"
                    self._emit("warning", target)
                    continue

                target.state = HealthState.CRITICAL
                target.failures += 1
                target.last_reason = "engine stalled"

                try:
                    self.logger.warning(
                        f"[WATCHDOG] {target.name} stalled"
                    )
                except Exception:
                    pass

                if target.restart_callback:
                    try:
                        target.restart_callback()
                    except Exception:
                        pass

                self._emit("critical", target)

    def snapshot(self):
        return {
            t.name: {
                "state": t.state.name,
                "checks": t.checks,
                "failures": t.failures,
                "last_seen": t.last_seen,
                "reason": t.last_reason,
            }
            for t in self._targets.values()
        }

    def healthy(self):
        return all(
            t.state != HealthState.CRITICAL
            for t in self._targets.values()
        )

    def clear(self):
        with self._lock:
            self._targets.clear()
                    
