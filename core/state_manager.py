"""
state_manager.py
CARRERA-HUB v2
Phase 3.1 Foundation
"""

from __future__ import annotations

import copy
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional


class RuntimeState(Enum):
    STARTING=auto()
    RUNNING=auto()
    PAUSED=auto()
    STOPPING=auto()
    STOPPED=auto()
    ERROR=auto()


class PackageState(Enum):
    OFFLINE=auto()
    LAUNCHING=auto()
    VERIFYING=auto()
    JOINING=auto()
    ONLINE=auto()
    RECOVERING=auto()
    COOLDOWN=auto()
    ERROR=auto()


class HealthState(Enum):
    HEALTHY=auto()
    WARNING=auto()
    UNSTABLE=auto()
    CRITICAL=auto()


class RecoveryState(Enum):
    IDLE=auto()
    WAITING=auto()
    RUNNING=auto()
    SUCCESS=auto()
    FAILED=auto()
    COOLDOWN=auto()


@dataclass
class PackageContext:
    package_name:str
    enabled:bool=True
    priority:int=0
    pid:Optional[int]=None
    state:PackageState=PackageState.OFFLINE
    health:HealthState=HealthState.HEALTHY
    recovery_state:RecoveryState=RecoveryState.IDLE
    current_error:Optional[int]=None
    launch_count:int=0
    recovery_count:int=0
    crash_count:int=0
    last_error_time:float=0.0
    last_recovery_time:float=0.0
    cooldown_until:float=0.0
    session_started:float=field(default_factory=time.time)
    private_server:str=""


class RuntimeStatistics:
    def __init__(self):
        self.total_launches=0
        self.total_recoveries=0
        self.total_crashes=0

    def snapshot(self):
        return {
            "launches":self.total_launches,
            "recoveries":self.total_recoveries,
            "crashes":self.total_crashes,
        }


class StateManager:

    def __init__(self):
        self._lock=threading.RLock()
        self._runtime_state=RuntimeState.STARTING
        self._packages:Dict[str,PackageContext]={}
        self._stats=RuntimeStatistics()
        self._callbacks:List[Callable]=[]

    def subscribe(self,callback:Callable):
        self._callbacks.append(callback)

    def _emit(self,event:str,pkg:str|None=None):
        for cb in list(self._callbacks):
            try:
                cb(event,pkg)
            except Exception:
                pass

    def set_runtime_state(self,state:RuntimeState):
        with self._lock:
            self._runtime_state=state
            self._emit("runtime_state_changed")

    def get_runtime_state(self):
        return self._runtime_state

    def add_package(self,package_name:str,priority:int=0):
        with self._lock:
            if package_name not in self._packages:
                self._packages[package_name]=PackageContext(
                    package_name=package_name,
                    priority=priority
                )
                self._emit("package_added",package_name)

    def remove_package(self,package_name:str):
        with self._lock:
            self._packages.pop(package_name,None)
            self._emit("package_removed",package_name)

    def get_package(self,package_name:str)->Optional[PackageContext]:
        return self._packages.get(package_name)

    def update_state(self,package_name:str,state:PackageState):
        with self._lock:
            ctx=self._packages[package_name]
            ctx.state=state
            self._emit("package_state_changed",package_name)

    def update_pid(self,package_name:str,pid:Optional[int]):
        with self._lock:
            self._packages[package_name].pid=pid

    def record_launch(self,package_name:str):
        with self._lock:
            ctx=self._packages[package_name]
            ctx.launch_count+=1
            self._stats.total_launches+=1

    def record_recovery(self,package_name:str):
        with self._lock:
            ctx=self._packages[package_name]
            ctx.recovery_count+=1
            ctx.last_recovery_time=time.time()
            self._stats.total_recoveries+=1

    def record_crash(self,package_name:str,error:Optional[int]=None):
        with self._lock:
            ctx=self._packages[package_name]
            ctx.crash_count+=1
            ctx.current_error=error
            ctx.last_error_time=time.time()
            self._stats.total_crashes+=1

    def snapshot(self):
        with self._lock:
            return {
                "runtime_state":self._runtime_state.name,
                "statistics":self._stats.snapshot(),
                "packages":copy.deepcopy(self._packages)
            }

    def reset(self):
        with self._lock:
            self._packages.clear()
            self._stats=RuntimeStatistics()
            self._runtime_state=RuntimeState.STARTING
            self._emit("reset")
