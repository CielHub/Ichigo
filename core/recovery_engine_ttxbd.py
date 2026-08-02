"""
recovery_engine.py
CARRERA-HUB v2
Phase 3.4 - Recovery Engine
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum, auto


class RecoveryStatus(Enum):
    IDLE = auto()
    PREPARING = auto()
    FORCE_STOP = auto()
    WAITING = auto()
    RELAUNCH = auto()
    VERIFYING = auto()
    SUCCESS = auto()
    FAILED = auto()


@dataclass
class RecoveryResult:
    package: str
    success: bool
    status: RecoveryStatus
    message: str = ""
    elapsed: float = 0.0


class RecoveryEngine:
    """
    Execute recovery tasks.

    Responsibilities:
    - Force stop package
    - Wait configured delay
    - Relaunch package
    - Verify launch
    - Update scheduler/state
    """

    def __init__(
        self,
        config_manager,
        state_manager,
        android_service,
        logger,
        launcher_engine,
        verification_engine,
        recovery_scheduler,
    ):
        self.config = config_manager
        self.state = state_manager
        self.android = android_service
        self.logger = logger
        self.launcher = launcher_engine
        self.verifier = verification_engine
        self.scheduler = recovery_scheduler
        self._lock = threading.RLock()

    def recover(self, task):
        start = time.time()

        with self._lock:
            package = task.package

            try:
                self.logger.recovery_event(package, "START")
            except Exception:
                pass

            try:
                self.state.record_recovery(package)
            except Exception:
                pass

            try:
                self.android.process.force_stop(package)
            except Exception as exc:
                self.scheduler.finish(package, False)
                return RecoveryResult(
                    package=package,
                    success=False,
                    status=RecoveryStatus.FAILED,
                    message=str(exc),
                    elapsed=time.time() - start,
                )

            delay = self.config.get("recovery", "delay", default=10)
            time.sleep(delay)

            launch = self.launcher.launch(package)
            if not launch.success:
                self.scheduler.finish(package, False)
                return RecoveryResult(
                    package=package,
                    success=False,
                    status=RecoveryStatus.FAILED,
                    message="Launch failed",
                    elapsed=time.time() - start,
                )

            verify = self.verifier.verify(package)
            if not verify.success:
                self.scheduler.finish(package, False)
                return RecoveryResult(
                    package=package,
                    success=False,
                    status=RecoveryStatus.FAILED,
                    message="Verification failed",
                    elapsed=time.time() - start,
                )

            self.scheduler.finish(package, True)

            try:
                self.logger.recovery_event(package, "SUCCESS")
            except Exception:
                pass

            return RecoveryResult(
                package=package,
                success=True,
                status=RecoveryStatus.SUCCESS,
                message="Recovery completed",
                elapsed=time.time() - start,
            )
