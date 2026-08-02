"""
monitor_engine.py
CARRERA-HUB v2
Phase 3.3 - Health Monitor Engine
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List


class MonitorStatus(Enum):
    STOPPED=auto()
    RUNNING=auto()
    PAUSED=auto()


@dataclass
class MonitorResult:
    package:str
    pid_alive:bool
    process_alive:bool
    timestamp:float
    message:str=""


class MonitorEngine:
    """
    Health monitor only.

    Responsibilities:
    - Check package health
    - Update StateManager
    - Emit monitor events

    Does NOT:
    - Launch
    - Recover
    - Kill process
    """

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
        self._status=MonitorStatus.STOPPED
        self._callbacks:List[Callable]=[]

    def subscribe(self,callback:Callable):
        self._callbacks.append(callback)

    def _emit(self,event:str,package:str,result:MonitorResult):
        for cb in list(self._callbacks):
            try:
                cb(event,package,result)
            except Exception:
                pass

    def start(self):
        self._status=MonitorStatus.RUNNING

    def stop(self):
        self._status=MonitorStatus.STOPPED

    def status(self):
        return self._status

    def check_package(self,package_name:str)->MonitorResult:
        pid_ok=False
        process_ok=False

        try:
            pid=self.android.process.pidof(package_name)
            pid_ok=pid.success and bool(pid.stdout)
        except Exception:
            pass

        try:
            ps=self.android.process.ps()
            process_ok=ps.success and package_name in ps.stdout
        except Exception:
            pass

        result=MonitorResult(
            package=package_name,
            pid_alive=pid_ok,
            process_alive=process_ok,
            timestamp=time.time(),
            message="ONLINE" if pid_ok else "OFFLINE"
        )

        try:
            if pid_ok:
                self.state.update_pid(package_name,int(pid.stdout.split()[0]))
            else:
                self.state.update_pid(package_name,None)
        except Exception:
            pass

        self._emit("health_checked",package_name,result)
        return result

    def check_all(self)->Dict[str,MonitorResult]:
        results={}
        for profile in self.registry.enabled():
            results[profile.package_name]=self.check_package(profile.package_name)
        return results
