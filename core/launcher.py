"""
launcher.py
CARRERA-HUB v2
Phase 3.2 - Launcher Engine (Foundation)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class LaunchState(Enum):
    IDLE=auto()
    BUILDING_INTENT=auto()
    LAUNCHING=auto()
    VERIFYING=auto()
    SUCCESS=auto()
    FAILED=auto()


@dataclass
class LaunchResult:
    package:str
    success:bool
    state:LaunchState
    message:str=""
    elapsed:float=0.0


class LauncherEngine:

    def __init__(
        self,
        config_manager,
        state_manager,
        android_service,
        logger,
        package_registry,
    ):
        self.config=config_manager
        self.state=state_manager
        self.android=android_service
        self.logger=logger
        self.registry=package_registry
        self._lock=threading.RLock()

    def launch(self, package_name:str)->LaunchResult:
        start=time.time()

        with self._lock:
            self.logger.launch_event(package_name)

            profile=self.registry.get(package_name)
            if profile is None:
                return LaunchResult(
                    package_name,
                    False,
                    LaunchState.FAILED,
                    "Package not registered",
                    time.time()-start,
                )

            try:
                self.state.update_state(package_name, self.state.get_package(package_name).state.LAUNCHING)
            except Exception:
                pass

            try:
                result=self.android.intent.launch_package(package_name)
            except Exception as exc:
                return LaunchResult(
                    package_name,
                    False,
                    LaunchState.FAILED,
                    str(exc),
                    time.time()-start,
                )

            if not result.success:
                self.logger.error(f"Launch failed: {package_name}")
                return LaunchResult(
                    package_name,
                    False,
                    LaunchState.FAILED,
                    result.stderr,
                    time.time()-start,
                )

            delay=self.config.get("launcher","delay",default=5)
            time.sleep(delay)

            verify=self.verify(package_name)

            if verify:
                try:
                    self.state.record_launch(package_name)
                except Exception:
                    pass

                return LaunchResult(
                    package_name,
                    True,
                    LaunchState.SUCCESS,
                    "Launch successful",
                    time.time()-start,
                )

            return LaunchResult(
                package_name,
                False,
                LaunchState.FAILED,
                "Verification failed",
                time.time()-start,
            )

    def verify(self,package_name:str)->bool:
        try:
            result=self.android.process.pidof(package_name)
            return result.success and bool(result.stdout)
        except Exception:
            return False

    def relaunch(self,package_name:str)->LaunchResult:
        self.android.process.force_stop(package_name)
        delay=self.config.get("recovery","delay",default=10)
        time.sleep(delay)
        return self.launch(package_name)
