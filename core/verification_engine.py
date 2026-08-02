
"""
verification_engine.py
CARRERA-HUB v2
Enhanced Verification Engine
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum, auto


class VerificationState(Enum):
    PENDING=auto()
    RUNNING=auto()
    SUCCESS=auto()
    FAILED=auto()
    TIMEOUT=auto()


@dataclass
class VerificationResult:
    package:str
    success:bool
    state:VerificationState
    reason:str=""
    elapsed:float=0.0


class VerificationEngine:
    """
    Verifies that a Roblox package is actually running
    after launch or recovery.
    """

    def __init__(self,config,state_manager,android_service,logger):
        self.config=config
        self.state=state_manager
        self.android=android_service
        self.logger=logger
        self._lock=threading.RLock()

    def _process_alive(self,package:str)->bool:
        try:
            result=self.android.process.pidof(package)
            return result.success and bool(result.stdout.strip())
        except Exception:
            return False

    def _activity_alive(self,package:str)->bool:
        try:
            result=self.android.activity.current(package)
            return result.success
        except Exception:
            return False

    def verify(self,package:str)->VerificationResult:
        timeout=self.config.get(
            "verification",
            "timeout",
            default=30
        )

        interval=self.config.get(
            "verification",
            "poll_interval",
            default=1
        )

        start=time.time()

        with self._lock:
            while time.time()-start<timeout:

                process_ok=self._process_alive(package)
                activity_ok=self._activity_alive(package)

                if process_ok or activity_ok:
                    try:
                        self.state.mark_online(package)
                    except Exception:
                        pass

                    try:
                        self.logger.info(
                            f"[VERIFY] {package} verified"
                        )
                    except Exception:
                        pass

                    return VerificationResult(
                        package,
                        True,
                        VerificationState.SUCCESS,
                        "Package verified",
                        time.time()-start
                    )

                time.sleep(interval)

            try:
                self.state.mark_offline(package)
            except Exception:
                pass

            try:
                self.logger.warning(
                    f"[VERIFY] {package} timeout"
                )
            except Exception:
                pass

            return VerificationResult(
                package,
                False,
                VerificationState.TIMEOUT,
                "Verification timeout",
                time.time()-start
            )

    def verify_all(self,registry):
        results=[]
        for profile in registry.enabled():
            results.append(
                self.verify(profile.package_name)
            )
        return results
        
