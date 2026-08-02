"""
package_context.py
CARRERA-HUB v2
Phase 3.1 - Runtime Package Context
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class PackageState(Enum):
    OFFLINE = auto()
    LAUNCHING = auto()
    VERIFYING = auto()
    JOINING = auto()
    ONLINE = auto()
    ERROR = auto()
    RECOVERING = auto()
    COOLDOWN = auto()


class HealthState(Enum):
    HEALTHY = auto()
    WARNING = auto()
    UNSTABLE = auto()
    CRITICAL = auto()


class RecoveryState(Enum):
    IDLE = auto()
    WAITING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    COOLDOWN = auto()


@dataclass
class RuntimeMetrics:
    launch_count: int = 0
    recovery_count: int = 0
    crash_count: int = 0
    verification_count: int = 0
    detector_hits: int = 0
    successful_joins: int = 0
    total_uptime: float = 0.0


@dataclass
class SessionInfo:
    started_at: float = field(default_factory=time.time)
    last_launch: float = 0.0
    last_join: float = 0.0
    last_recovery: float = 0.0
    last_error: float = 0.0
    session_id: str = ""


@dataclass
class CooldownInfo:
    active: bool = False
    until: float = 0.0
    reason: str = ""


@dataclass
class PackageContext:
    package_name: str

    enabled: bool = True
    priority: int = 0

    pid: Optional[int] = None
    process_alive: bool = False

    state: PackageState = PackageState.OFFLINE
    health: HealthState = HealthState.HEALTHY
    recovery_state: RecoveryState = RecoveryState.IDLE

    current_error: Optional[int] = None
    last_error_message: str = ""

    private_server_link: str = ""

    metrics: RuntimeMetrics = field(default_factory=RuntimeMetrics)
    session: SessionInfo = field(default_factory=SessionInfo)
    cooldown: CooldownInfo = field(default_factory=CooldownInfo)

    runtime_flags: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def mark_online(self):
        self.state = PackageState.ONLINE
        self.process_alive = True

    def mark_offline(self):
        self.state = PackageState.OFFLINE
        self.process_alive = False
        self.pid = None

    def mark_error(self, code: Optional[int], message: str = ""):
        self.current_error = code
        self.last_error_message = message
        self.session.last_error = time.time()
        self.metrics.crash_count += 1
        self.state = PackageState.ERROR

    def begin_recovery(self):
        self.recovery_state = RecoveryState.RUNNING
        self.state = PackageState.RECOVERING
        self.metrics.recovery_count += 1
        self.session.last_recovery = time.time()

    def finish_recovery(self, success: bool):
        self.recovery_state = (
            RecoveryState.SUCCESS if success else RecoveryState.FAILED
        )

    def snapshot(self) -> Dict[str, Any]:
        return {
            "package_name": self.package_name,
            "enabled": self.enabled,
            "priority": self.priority,
            "pid": self.pid,
            "process_alive": self.process_alive,
            "state": self.state.name,
            "health": self.health.name,
            "recovery_state": self.recovery_state.name,
            "current_error": self.current_error,
            "metrics": vars(self.metrics).copy(),
            "cooldown": vars(self.cooldown).copy(),
        }
