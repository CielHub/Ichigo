
"""
scheduler_engine.py
CARRERA-HUB v2
Enhanced Scheduler Engine
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Dict, Optional


class TaskPriority(IntEnum):
    CRITICAL=0
    HIGH=10
    NORMAL=20
    LOW=30


@dataclass
class ScheduledTask:
    name:str
    callback:Callable
    interval:float
    priority:int=TaskPriority.NORMAL
    enabled:bool=True
    last_run:float=0.0
    next_run:float=field(default_factory=time.monotonic)
    run_count:int=0
    error_count:int=0
    total_runtime:float=0.0


class SchedulerEngine:

    def __init__(self, logger=None):
        self.logger=logger
        self._tasks:Dict[str,ScheduledTask]={}
        self._lock=threading.RLock()
        self._running=False
        self._thread:Optional[threading.Thread]=None
        self._tick=0.1

    def register(self,name,callback,interval,
                 priority=TaskPriority.NORMAL):
        with self._lock:
            self._tasks[name]=ScheduledTask(
                name=name,
                callback=callback,
                interval=max(0.1,float(interval)),
                priority=int(priority)
            )

    def unregister(self,name):
        with self._lock:
            self._tasks.pop(name,None)

    def enable(self,name):
        if name in self._tasks:
            self._tasks[name].enabled=True

    def disable(self,name):
        if name in self._tasks:
            self._tasks[name].enabled=False

    def start(self):
        if self._running:
            return
        self._running=True
        self._thread=threading.Thread(
            target=self._loop,
            daemon=True,
            name="SchedulerEngine"
        )
        self._thread.start()

    def stop(self):
        self._running=False
        if self._thread:
            self._thread.join(timeout=3)

    def tick(self):
        self._execute_due_tasks()

    def _loop(self):
        while self._running:
            self._execute_due_tasks()
            time.sleep(self._tick)

    def _execute_due_tasks(self):
        now=time.monotonic()

        with self._lock:
            due=[
                t for t in self._tasks.values()
                if t.enabled and now>=t.next_run
            ]

        due.sort(key=lambda x:(x.priority,x.next_run))

        for task in due:
            start=time.monotonic()
            try:
                task.callback()
            except Exception as exc:
                task.error_count+=1
                if self.logger:
                    try:
                        self.logger.exception(
                            f"[SCHEDULER] {task.name}: {exc}"
                        )
                    except Exception:
                        pass
            finally:
                elapsed=time.monotonic()-start
                task.total_runtime+=elapsed
                task.run_count+=1
                task.last_run=now
                # drift resistant scheduling
                task.next_run=max(task.next_run+task.interval,
                                  time.monotonic()+0.001)

    def snapshot(self):
        with self._lock:
            return {
                name:{
                    "enabled":t.enabled,
                    "interval":t.interval,
                    "run_count":t.run_count,
                    "error_count":t.error_count,
                    "last_run":t.last_run,
                    "next_run":t.next_run,
                    "avg_runtime":(
                        t.total_runtime/t.run_count
                        if t.run_count else 0
                    )
                }
                for name,t in self._tasks.items()
            }

    def clear(self):
        with self._lock:
            self._tasks.clear()
            
