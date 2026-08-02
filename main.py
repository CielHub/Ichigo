"""
main.py
CARRERA-HUB v2
Phase 3.5 - Application Entry Point
"""

from __future__ import annotations

import signal
import sys
import time

from config_manager import ConfigManager
from state_manager import StateManager
from logger import LoggerManager
from android_service import AndroidService
from package_registry import PackageRegistry
from runtime_coordinator import RuntimeCoordinator
from scheduler_engine import SchedulerEngine
from monitor_engine import MonitorEngine
from error_detection_engine import ErrorDetectionEngine
from recovery_scheduler import RecoveryScheduler
from recovery_engine import RecoveryEngine
from verification_engine import VerificationEngine
from launcher import LauncherEngine
from private_server_engine import PrivateServerEngine
from watchdog_engine import WatchdogEngine
from dashboard import DashboardEngine


class CarreraHubApplication:

    def __init__(self):
        self.config=ConfigManager()
        self.state=StateManager()
        self.logger=LoggerManager()
        self.android=AndroidService()
        self.registry=PackageRegistry()

        self.scheduler=SchedulerEngine(self.logger)
        self.coordinator=RuntimeCoordinator(
            self.config,
            self.state,
            self.logger,
            self.android,
            self.registry
        )

        self.verifier=VerificationEngine(
            self.config,self.state,self.android,self.logger
        )

        self.launcher=LauncherEngine(
            self.config,self.state,self.android,
            self.logger,self.registry
        )

        self.monitor=MonitorEngine(
            self.config,self.state,self.android,
            self.logger,self.registry
        )

        self.detector=ErrorDetectionEngine(
            self.config,self.state,self.android,self.logger
        )

        self.recovery_scheduler=RecoveryScheduler(
            self.config,self.state,self.logger
        )

        self.recovery=RecoveryEngine(
            self.config,self.state,self.android,
            self.logger,self.launcher,
            self.verifier,self.recovery_scheduler
        )

        self.private_server=PrivateServerEngine(
            self.config,self.state,self.android,
            self.logger,self.verifier
        )

        self.watchdog=WatchdogEngine(
            self.config,self.state,self.logger
        )

        self.dashboard=DashboardEngine(
            self.config,self.state,self.logger,
            self.recovery_scheduler
        )

    def register_tasks(self):
        self.scheduler.register(
            "monitor",
            self.monitor.check_all,
            self.config.get("monitor","interval",default=15)
        )
        self.scheduler.register(
            "watchdog",
            self.watchdog.scan,
            5
        )

    def initialize(self):
        self.coordinator.initialize()
        self.register_tasks()

    def start(self):
        self.coordinator.start()
        self.scheduler.start()
        self.dashboard.render()

    def stop(self):
        self.scheduler.stop()
        self.coordinator.stop()


app=CarreraHubApplication()


def shutdown(*_):
    app.logger.info("Shutting down...")
    app.stop()
    sys.exit(0)


signal.signal(signal.SIGINT,shutdown)
signal.signal(signal.SIGTERM,shutdown)


def main():
    app.initialize()
    app.start()

    while True:
        time.sleep(1)


if __name__=="__main__":
    main()
