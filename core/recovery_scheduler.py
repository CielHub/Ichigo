
"""
recovery_scheduler.py
CARRERA-HUB v2
Enhanced Recovery Scheduler
"""

from __future__ import annotations

import heapq
import threading
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Dict, List, Optional


class RecoveryPriority(IntEnum):
    LOW=30
    NORMAL=20
    HIGH=10
    CRITICAL=0


@dataclass(order=True)
class RecoveryTask:
    priority:int
    created_at:float
    package:str=field(compare=False)
    reason:str=field(compare=False)
    retries:int=field(default=0,compare=False)


class RecoveryScheduler:

    def __init__(self,config,state_manager,logger):
        self.config=config
        self.state=state_manager
        self.logger=logger

        self._lock=threading.RLock()
        self._queue=[]
        self._running={}
        self._cooldowns={}
        self._callbacks=[]
        self._retry_counter={}

    def subscribe(self,callback:Callable):
        self._callbacks.append(callback)

    def _emit(self,event:str,task:RecoveryTask):
        for cb in list(self._callbacks):
            try:
                cb(event,task)
            except Exception:
                pass

    def request(self,package:str,reason:str,
                priority:RecoveryPriority=RecoveryPriority.NORMAL):

        with self._lock:
            if package in self._running:
                return False

            now=time.time()

            if now<self._cooldowns.get(package,0):
                return False

            for task in self._queue:
                if task.package==package:
                    return False

            heapq.heappush(
                self._queue,
                RecoveryTask(
                    priority=int(priority),
                    created_at=now,
                    package=package,
                    reason=reason
                )
            )

            try:
                self.logger.info(
                    f"[RECOVERY] queued {package} ({reason})"
                )
            except Exception:
                pass

            self._emit("queued",self._queue[0])
            return True

    def next_task(self)->Optional[RecoveryTask]:
        with self._lock:
            if not self._queue:
                return None

            task=heapq.heappop(self._queue)
            self._running[task.package]=task
            self._emit("started",task)
            return task

    def finish(self,package:str,success:bool):
        with self._lock:
            task=self._running.pop(package,None)
            if task is None:
                return

            cooldown=self.config.get(
                "recovery",
                "cooldown",
                default=30
            )

            self._cooldowns[package]=time.time()+cooldown

            if success:
                self._retry_counter[package]=0
            else:
                self._retry_counter[package]=(
                    self._retry_counter.get(package,0)+1
                )

            try:
                self.logger.info(
                    f"[RECOVERY] finished {package} success={success}"
                )
            except Exception:
                pass

            self._emit("finished",task)

    def retry_count(self,package:str)->int:
        return self._retry_counter.get(package,0)

    def queue_size(self):
        return len(self._queue)

    def running_packages(self):
        return list(self._running.keys())

    def snapshot(self):
        return {
            "queued":len(self._queue),
            "running":list(self._running.keys()),
            "cooldowns":dict(self._cooldowns),
            "retries":dict(self._retry_counter)
        }

    def clear(self):
        with self._lock:
            self._queue.clear()
            self._running.clear()
            self._cooldowns.clear()
            self._retry_counter.clear()
            
