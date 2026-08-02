
"""
main.py
CARRERA-HUB v2
Integrated Bootstrap
"""

from __future__ import annotations

import signal
import sys

from core.config_manager import ConfigManager
from core.state_manager import StateManager
from core.logger import LoggerManager
from core.android_service import AndroidService
from core.package_registry import PackageRegistry
from core.package_manager import PackageManager
from core.private_server_manager import PrivateServerManager

from core.runtime_coordinator import RuntimeCoordinator
from core.scheduler_engine import SchedulerEngine
from core.monitor_engine import MonitorEngine
from core.error_detection_engine import ErrorDetectionEngine
from core.recovery_scheduler import RecoveryScheduler
from core.recovery_engine import RecoveryEngine
from core.verification_engine import VerificationEngine
from core.launcher import LauncherEngine
from core.private_server_engine import PrivateServerEngine
from core.watchdog_engine import WatchdogEngine
from core.dashboard import DashboardEngine
from core.menu import MenuEngine


class CarreraHubApplication:

    def __init__(self):
        # Core
        self.config=ConfigManager()
        self.state=StateManager()
        self.logger=LoggerManager()
        self.android=AndroidService()
        self.registry=PackageRegistry()

        # Managers
        self.package_manager=PackageManager(
            self.android,self.registry,self.config,self.logger
        )

        self.private_server_manager=PrivateServerManager(
            self.config,self.logger
        )
        self.private_server_manager.load()

        # Engines
        self.scheduler=SchedulerEngine(self.logger)

        self.verifier=VerificationEngine(
            self.config,self.state,self.android,self.logger
        )

        self.launcher=LauncherEngine(
            self.config,
            self.state,
            self.android,
            self.logger,
            self.registry,
            self.private_server_manager,
            self.verifier,
        )

        self.recovery_scheduler=RecoveryScheduler(
            self.config,self.state,self.logger
        )

        self.recovery=RecoveryEngine(
            self.config,
            self.state,
            self.android,
            self.logger,
            self.launcher,
            self.verifier,
            self.recovery_scheduler,
            self.private_server_manager,
        )

        self.monitor=MonitorEngine(
            self.config,
            self.state,
            self.android,
            self.logger,
            self.registry,
            self.verifier,
            self.recovery_scheduler,
        )

        self.detector=ErrorDetectionEngine(
            self.config,
            self.state,
            self.android,
            self.logger,
            self.recovery_scheduler,
        )

        self.watchdog=WatchdogEngine(
            self.config,self.state,self.logger
        )

        self.dashboard=DashboardEngine(
            self.config,
            self.state,
            self.logger,
            self.recovery_scheduler,
        )

        self.private_server_engine=PrivateServerEngine(
            self.config,self.state,self.android,self.logger,self.verifier
        )

        # Runtime
        self.runtime=RuntimeCoordinator(
            self.config,
            self.state,
            self.logger,
            self.android,
            self.registry,
        )

        self._register_runtime_engines()
        self._register_scheduler_tasks()

        self.menu=MenuEngine(self)

    def _register_runtime_engines(self):
        self.runtime.register_engine("scheduler", self.scheduler)
        self.runtime.register_engine("monitor", self.monitor)
        self.runtime.register_engine("detector", self.detector)
        self.runtime.register_engine("recovery", self.recovery)
        self.runtime.register_engine("watchdog", self.watchdog)

    def _register_scheduler_tasks(self):
        self.scheduler.register(
            "monitor",
            self.monitor.check_all,
            self.config.get("monitor","interval",default=15)
        )
        self.scheduler.register(
            "detector",
            lambda: self.detector.scan_all(self.registry),
            self.config.get("error_detection","interval",default=3)
        )
        self.scheduler.register(
            "recovery",
            self.recovery.recover_pending,
            self.config.get("recovery","interval",default=2)
        )
        self.scheduler.register(
            "watchdog",
            self.watchdog.scan,
            self.config.get("watchdog","interval",default=5)
        )

    def start(self):
        self.runtime.initialize()
        self.scheduler.start()
        self.runtime.start()

    def stop(self):
        self.runtime.stop()
        self.scheduler.stop()

    def run(self):
        self.menu.loop()


app=CarreraHubApplication()

def shutdown(*_):
    app.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

if __name__=="__main__":
    app.run()
    
