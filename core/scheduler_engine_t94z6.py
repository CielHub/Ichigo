"""
scheduler_engine.py
CARRERA-HUB v2
Phase 3.5 - Scheduler Engine
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, Optional


class TaskStatus(Enum):
    IDLE=auto()
    RUNNING=auto()
    PAUSED=auto()
    DISABLED=auto()


@dataclass
class ScheduledTask:
    name:str
    callback:Callable
    interval:float
    enabled:bool=True
    last_run:float=0.0
    next_run:float=field(default_factory=time.time)
    status:TaskStatus=TaskStatus.IDLE
    run_count:int=0
    error_count:int=0


class SchedulerEngine:
    """
    Central scheduler.

    Executes registered engine callbacks
    independently according to their intervals.
    """

    def __init__(self, logger=None):
        self.logger=logger
        self._lock=threading.RLock()
        self._tasks:Dict[str,ScheduledTask]={}
        self._running=False
        self._thread:Optional[threading.Thread]=None

    def register(self,name:str,callback:Callable,interval:float):
        with self._lock:
            self._tasks[name]=ScheduledTask(
                name=name,
                callback=callback,
                interval=interval,
                next_run=time.time()+interval
            )

    def unregister(self,name:str):
        with self._lock:
            self._tasks.pop(name,None)

    def enable(self,name:str):
        if name in self._tasks:
            self._tasks[name].enabled=True

    def disable(self,name:str):
        if name in self._tasks:
            self._tasks[name].enabled=False

    def _tick(self):
        while self._running:
            now=time.time()

            with self._lock:
                tasks=list(self._tasks.values())

            for task in tasks:
                if not task.enabled:
                    continue
                if now<task.next_run:
                    continue

                task.status=TaskStatus.RUNNING
                try:
                    task.callback()
                    task.run_count+=1
                    if self.logger:
                        self.logger.debug(f"[SCHEDULER] {task.name} executed")
                except Exception as exc:
                    task.error_count+=1
                    if self.logger:
                        self.logger.exception(f"[SCHEDULER] {task.name}: {exc}")
                finally:
                    task.status=TaskStatus.IDLE
                    task.last_run=now
                    task.next_run=now+task.interval

            time.sleep(0.05)

    def start(self):
        if self._running:
            return
        self._running=True
        self._thread=threading.Thread(target=self._tick,daemon=True)
        self._thread.start()

    def stop(self):
        self._running=False
        if self._thread:
            self._thread.join(timeout=1)

    def snapshot(self):
        return {
            n:{
                "interval":t.interval,
                "enabled":t.enabled,
                "status":t.status.name,
                "run_count":t.run_count,
                "error_count":t.error_count,
                "last_run":t.last_run,
                "next_run":t.next_run
            }
            for n,t in self._tasks.items()
        }
