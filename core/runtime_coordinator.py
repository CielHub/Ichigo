
"""
runtime_coordinator.py
CARRERA-HUB v2
Runtime Orchestrator (Foundation)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List


class RuntimeState(Enum):
    BOOTING=auto()
    INITIALIZING=auto()
    READY=auto()
    STARTING=auto()
    RUNNING=auto()
    STOPPING=auto()
    STOPPED=auto()
    ERROR=auto()


@dataclass
class RuntimeEvent:
    name:str
    timestamp:float=field(default_factory=time.time)
    payload:dict=field(default_factory=dict)


class RuntimeCoordinator:

    def __init__(self,config,state,logger,android,registry):
        self.config=config
        self.state=state
        self.logger=logger
        self.android=android
        self.registry=registry

        self.runtime_state=RuntimeState.BOOTING
        self._engines:Dict[str,object]={}
        self._callbacks:Dict[str,List[Callable]]={}
        self._worker=None
        self._running=False
        self._lock=threading.RLock()
        self._heartbeat={}

    def register_engine(self,name:str,engine):
        self._engines[name]=engine

    def engine(self,name):
        return self._engines.get(name)

    def subscribe(self,event:str,callback:Callable):
        self._callbacks.setdefault(event,[]).append(callback)

    def emit(self,event:str,**payload):
        evt=RuntimeEvent(event,payload=payload)
        for cb in self._callbacks.get(event,[]):
            try:
                cb(evt)
            except Exception:
                pass

    def initialize(self):
        with self._lock:
            self.runtime_state=RuntimeState.INITIALIZING

            self._validate_environment()
            self._load_configuration()
            self._restore_runtime()

            self.runtime_state=RuntimeState.READY
            self.emit("ready")

    def _validate_environment(self):
        checks=[
            ("am",self.android.shell.which("am")),
            ("pm",self.android.shell.which("pm")),
            ("pidof",self.android.shell.which("pidof")),
            ("logcat",self.android.shell.which("logcat")),
        ]

        missing=[name for name,result in checks if not result.success]
        if missing:
            raise RuntimeError(
                f"Missing Android tools: {', '.join(missing)}"
            )

    def _load_configuration(self):
        try:
            self.config.load()
        except Exception:
            pass

    def _restore_runtime(self):
        try:
            self.state.restore()
        except Exception:
            pass

    def start(self):
        with self._lock:
            if self._running:
                return

            self.runtime_state=RuntimeState.STARTING
            self._running=True

            self._worker=threading.Thread(
                target=self._runtime_loop,
                daemon=True,
                name="RuntimeCoordinator"
            )
            self._worker.start()

    def stop(self):
        with self._lock:
            self.runtime_state=RuntimeState.STOPPING
            self._running=False

        if self._worker:
            self._worker.join(timeout=5)

        self._shutdown()
        self.runtime_state=RuntimeState.STOPPED
        self.emit("stopped")

    def _runtime_loop(self):
        self.runtime_state=RuntimeState.RUNNING

        scheduler=self.engine("scheduler")
        monitor=self.engine("monitor")
        detector=self.engine("detector")
        recovery=self.engine("recovery")
        watchdog=self.engine("watchdog")

        while self._running:

            if scheduler:
                scheduler.tick()

            if monitor:
                monitor.check_all()

            if detector:
                detector.scan_all(self.registry)

            if recovery:
                recovery.recover_pending()

            if watchdog:
                watchdog.scan()

            self._heartbeat["runtime"]=time.time()
            self.emit("heartbeat")
            time.sleep(0.2)

    def _shutdown(self):
        for name,engine in self._engines.items():
            try:
                if hasattr(engine,"stop"):
                    engine.stop()
            except Exception:
                pass

        try:
            self.state.save()
        except Exception:
            pass

        try:
            self.logger.shutdown()
        except Exception:
            pass

    def status(self):
        return {
            "state":self.runtime_state.name,
            "running":self._running,
            "engines":list(self._engines.keys()),
            "heartbeat":dict(self._heartbeat),
        }
        
