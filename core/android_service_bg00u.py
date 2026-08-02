"""
android_service.py
CARRERA-HUB v2
Phase 3.1 - Android Platform Layer
"""

from __future__ import annotations

import shlex
import subprocess
import threading
from dataclasses import dataclass
from typing import List, Optional


class AndroidServiceError(Exception):
    pass


@dataclass
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


class ShellService:
    def __init__(self):
        self._lock = threading.RLock()

    def run(self, command: str, timeout: int = 30) -> CommandResult:
        with self._lock:
            proc = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return CommandResult(
                command=command,
                returncode=proc.returncode,
                stdout=proc.stdout.strip(),
                stderr=proc.stderr.strip()
            )


class ProcessService:
    def __init__(self, shell: ShellService):
        self.shell = shell

    def pidof(self, package: str):
        return self.shell.run(f"pidof {package}")

    def ps(self):
        return self.shell.run("ps")

    def dumpsys_processes(self):
        return self.shell.run("dumpsys activity processes")

    def force_stop(self, package: str):
        return self.shell.run(f"am force-stop {package}")


class IntentService:
    def __init__(self, shell: ShellService):
        self.shell = shell

    def launch_package(self, package: str):
        return self.shell.run(f"monkey -p {package} -c android.intent.category.LAUNCHER 1")

    def open_uri(self, uri: str):
        return self.shell.run(
            f'am start -a android.intent.action.VIEW -d "{uri}"'
        )


class PackageService:
    def __init__(self, shell: ShellService):
        self.shell = shell

    def list_packages(self):
        return self.shell.run("pm list packages")

    def package_info(self, package: str):
        return self.shell.run(f"dumpsys package {package}")


class LogcatService:
    def __init__(self, shell: ShellService):
        self.shell = shell

    def clear(self):
        return self.shell.run("logcat -c")

    def dump(self):
        return self.shell.run("logcat -d")


class InputService:
    def __init__(self, shell: ShellService):
        self.shell = shell

    def tap(self, x: int, y: int):
        return self.shell.run(f"input tap {x} {y}")

    def text(self, value: str):
        escaped = value.replace(" ", "%s")
        return self.shell.run(f"input text {escaped}")

    def keyevent(self, keycode: int):
        return self.shell.run(f"input keyevent {keycode}")


class AndroidService:
    """
    Unified Android Platform Layer.

    All runtime modules should access Android only through this class.
    """

    def __init__(self):
        self.shell = ShellService()
        self.process = ProcessService(self.shell)
        self.intent = IntentService(self.shell)
        self.package = PackageService(self.shell)
        self.logcat = LogcatService(self.shell)
        self.input = InputService(self.shell)
