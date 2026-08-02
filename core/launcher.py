
"""
launcher.py
CARRERA-HUB v2
Enhanced Launcher Engine
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class LaunchState(Enum):
    IDLE=auto()
    PREPARING=auto()
    LAUNCHING=auto()
    JOINING_PRIVATE_SERVER=auto()
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
    """
    Launches only packages selected by PackageManager/PackageRegistry.

    Flow:
    Registry -> Launch -> PrivateServer -> Verify
    """

    def __init__(
        self,
        config_manager,
        state_manager,
        android_service,
        logger,
        package_registry,
        private_server_manager=None,
        verification_engine=None,
    ):
        self.config=config_manager
        self.state=state_manager
        self.android=android_service
        self.logger=logger
        self.registry=package_registry
        self.ps_manager=private_server_manager
        self.verifier=verification_engine
        self._lock=threading.RLock()

    def launch_package(self, package:str)->LaunchResult:
        start=time.time()

        try:
            self.logger.launch_event(package)
        except Exception:
            pass

        result=self.android.intent.launch_package(package)

        if not result.success:
            return LaunchResult(
                package,False,LaunchState.FAILED,
                result.stderr,time.time()-start
            )

        delay=self.config.get("launcher","startup_delay",default=5)
        time.sleep(delay)

        if self.ps_manager:
            profile=self.ps_manager.profile
            if profile.valid and profile.deep_link:
                self.android.intent.open_uri(profile.deep_link)

        if self.verifier:
            verify=self.verifier.verify(package)
            if not verify.success:
                return LaunchResult(
                    package,False,LaunchState.FAILED,
                    "Verification failed",
                    time.time()-start
                )

        try:
            self.state.record_launch(package)
        except Exception:
            pass

        return LaunchResult(
            package,True,LaunchState.SUCCESS,
            "Launch completed",
            time.time()-start
        )

    def launch_selected(self)->List[LaunchResult]:
        results=[]

        for profile in self.registry.enabled():
            results.append(
                self.launch_package(profile.package_name)
            )

        return results

    def relaunch_package(self,package:str)->LaunchResult:
        self.android.process.force_stop(package)

        delay=self.config.get(
            "recovery",
            "delay",
            default=10
        )

        time.sleep(delay)

        return self.launch_package(package)
        
