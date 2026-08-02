"""
verification_engine.py
CARRERA-HUB v2
Phase 3.2 - Verification Engine
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List


class VerificationStage(Enum):
    PID = auto()
    PROCESS = auto()
    ACTIVITY = auto()
    WINDOW = auto()
    READY = auto()


@dataclass
class VerificationResult:
    package: str
    success: bool
    completed_stages: List[str] = field(default_factory=list)
    failed_stage: str = ""
    message: str = ""
    elapsed: float = 0.0


class VerificationEngine:

    def __init__(self, config_manager, state_manager,
                 android_service, logger):
        self.config = config_manager
        self.state = state_manager
        self.android = android_service
        self.logger = logger
        self._lock = threading.RLock()

    def verify(self, package_name: str) -> VerificationResult:
        start = time.time()
        stages = []

        with self._lock:

            checks = [
                (VerificationStage.PID, self._verify_pid),
                (VerificationStage.PROCESS, self._verify_process),
                (VerificationStage.ACTIVITY, self._verify_activity),
                (VerificationStage.WINDOW, self._verify_window),
            ]

            for stage, func in checks:
                ok = func(package_name)
                if not ok:
                    self.logger.warning(
                        f"[VERIFY] {package_name} failed at {stage.name}"
                    )
                    return VerificationResult(
                        package=package_name,
                        success=False,
                        completed_stages=stages,
                        failed_stage=stage.name,
                        message=f"{stage.name} verification failed",
                        elapsed=time.time() - start,
                    )

                stages.append(stage.name)

            stages.append(VerificationStage.READY.name)

            self.logger.info(f"[VERIFY] {package_name} READY")

            return VerificationResult(
                package=package_name,
                success=True,
                completed_stages=stages,
                elapsed=time.time() - start,
            )

    def _verify_pid(self, package_name: str) -> bool:
        try:
            result = self.android.process.pidof(package_name)
            return result.success and bool(result.stdout)
        except Exception:
            return False

    def _verify_process(self, package_name: str) -> bool:
        try:
            result = self.android.process.ps()
            return result.success and package_name in result.stdout
        except Exception:
            return False

    def _verify_activity(self, package_name: str) -> bool:
        try:
            result = self.android.process.dumpsys_processes()
            return result.success and package_name in result.stdout
        except Exception:
            return False

    def _verify_window(self, package_name: str) -> bool:
        # Placeholder for future floating-window verification.
        return True

    def verify_many(self, packages: List[str]) -> Dict[str, VerificationResult]:
        return {pkg: self.verify(pkg) for pkg in packages}
