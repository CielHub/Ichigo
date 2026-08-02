"""
runtime_coordinator.py
CARRERA-HUB v2
Phase 3.1 - Runtime Coordinator
"""

from __future__ import annotations

import threading
from enum import Enum, auto
from typing import Callable, Dict, List, Optional


class CoordinatorState(Enum):
    CREATED = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()


class RuntimeCoordinator:
    """
    Coordinates lifecycle of the application.

    This class intentionally does not contain launcher,
    monitor, recovery or dashboard logic.
    It only orchestrates services.
    """

    def __init__(
        self,
        config_manager=None,
        state_manager=None,
        logger=None,
        android_service=None,
        package_registry=None,
    ):
        self._lock = threading.RLock()

        self.config = config_manager
        self.state = state_manager
        self.logger = logger
        self.android = android_service
        self.registry = package_registry

        self._state = CoordinatorState.CREATED
        self._services: Dict[str, object] = {}
        self._callbacks: List[Callable] = []

    # -----------------------------------------------------

    def register_service(self, name: str, service: object):
        with self._lock:
            self._services[name] = service

    def get_service(self, name: str):
        return self._services.get(name)

    def services(self):
        return dict(self._services)

    # -----------------------------------------------------

    def subscribe(self, callback: Callable):
        self._callbacks.append(callback)

    def _emit(self, event: str):
        for callback in list(self._callbacks):
            try:
                callback(event, self._state)
            except Exception:
                pass

    # -----------------------------------------------------

    def initialize(self):
        with self._lock:
            self._state = CoordinatorState.INITIALIZING
            self._emit("initializing")

            if self.config:
                self.config.load()

            self._state = CoordinatorState.READY
            self._emit("ready")

    def start(self):
        with self._lock:
            if self._state != CoordinatorState.READY:
                raise RuntimeError("Coordinator is not ready")

            self._state = CoordinatorState.RUNNING
            self._emit("running")

            if self.logger:
                try:
                    self.logger.info("Runtime Coordinator started.")
                except Exception:
                    pass

    def stop(self):
        with self._lock:
            self._state = CoordinatorState.STOPPING
            self._emit("stopping")

            self._state = CoordinatorState.STOPPED
            self._emit("stopped")

            if self.logger:
                try:
                    self.logger.info("Runtime Coordinator stopped.")
                except Exception:
                    pass

    def state_name(self):
        return self._state.name

    def state_enum(self):
        return self._state

    def snapshot(self):
        return {
            "coordinator_state": self._state.name,
            "registered_services": list(self._services.keys()),
            "service_count": len(self._services),
        }
