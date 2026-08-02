"""
recovery_scheduler.py
CARRERA-HUB v2
Phase 3.4 - Recovery Scheduler
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Deque, Dict, List, Optional


class RecoveryPriority(Enum):
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class RecoveryDecision(Enum):
    QUEUED = auto()
    SKIPPED = auto()
    COOLDOWN = auto()
    RUNNING = auto()


@dataclass
class RecoveryTask:
    package: str
    reason: str
    priority: RecoveryPriority = RecoveryPriority.NORMAL
    created_at: float = field(default_factory=time.time)
    retries: int = 0


class RecoveryScheduler:
    """
    Decides WHEN recovery may start.

    Responsibilities:
    - Queue recovery tasks
    - Prevent duplicate recovery
    - Enforce cooldown
    - Dispatch tasks to RecoveryEngine

    Does NOT perform recovery itself.
    """

    def __init__(self, config_manager, state_manager, logger):
        self.config = config_manager
        self.state = state_manager
        self.logger = logger

        self._lock = threading.RLock()
        self._queue: Deque[RecoveryTask] = deque()
        self._running: Dict[str, RecoveryTask] = {}
        self._cooldowns: Dict[str, float] = {}
        self._callbacks: List[Callable] = []

    def subscribe(self, callback: Callable):
        self._callbacks.append(callback)

    def _emit(self, event: str, task: RecoveryTask):
        for cb in list(self._callbacks):
            try:
                cb(event, task)
            except Exception:
                pass

    def request(self,
                package: str,
                reason: str,
                priority: RecoveryPriority = RecoveryPriority.NORMAL
                ) -> RecoveryDecision:

        with self._lock:

            if package in self._running:
                return RecoveryDecision.RUNNING

            now = time.time()
            cooldown_until = self._cooldowns.get(package, 0)

            if now < cooldown_until:
                return RecoveryDecision.COOLDOWN

            for task in self._queue:
                if task.package == package:
                    return RecoveryDecision.SKIPPED

            task = RecoveryTask(
                package=package,
                reason=reason,
                priority=priority
            )

            self._queue.append(task)

            try:
                self.logger.info(
                    f"[RECOVERY_SCHEDULER] queued {package} ({reason})"
                )
            except Exception:
                pass

            self._emit("queued", task)

            return RecoveryDecision.QUEUED

    def next_task(self) -> Optional[RecoveryTask]:
        with self._lock:
            if not self._queue:
                return None

            task = self._queue.popleft()
            self._running[task.package] = task

            self._emit("started", task)

            return task

    def finish(self, package: str, success: bool):
        with self._lock:

            task = self._running.pop(package, None)

            if task is None:
                return

            cooldown = self.config.get(
                "recovery",
                "cooldown",
                default=30
            )

            self._cooldowns[package] = time.time() + cooldown

            try:
                self.logger.info(
                    f"[RECOVERY_SCHEDULER] finished {package} success={success}"
                )
            except Exception:
                pass

            self._emit("finished", task)

    def queue_size(self) -> int:
        return len(self._queue)

    def running_packages(self) -> List[str]:
        return list(self._running.keys())

    def clear(self):
        with self._lock:
            self._queue.clear()
            self._running.clear()
            self._cooldowns.clear()

    def snapshot(self):
        return {
            "queued": len(self._queue),
            "running": list(self._running.keys()),
            "cooldowns": dict(self._cooldowns),
        }
