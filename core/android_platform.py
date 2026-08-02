"""
android_platform.py
===================

CARRERA-HUB v2
Phase 3.1 - Core Foundation

Android abstraction layer.

All Android shell interactions should go through this module.
"""

from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from typing import List


class AndroidCommandError(RuntimeError):
    pass


@dataclass
class CommandResult:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class ShellService:
    def __init__(self):
        self._lock = threading.RLock()

    def run(self, command: List[str], check: bool = False) -> CommandResult:
        with self._lock:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True
            )
            result = CommandResult(
                command=command,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr
            )
            if check and not result.ok:
                raise AndroidCommandError(result.stderr.strip())
            return result


class ProcessService:
    def __init__(self, shell: ShellService):
        self.shell = shell

    def pidof(self, package: str):
        result = self.shell.run(["pidof", package])
        return result.stdout.strip() if result.ok else ""


class PackageService:
    def __init__(self, shell: ShellService):
        self.shell = shell

    def list_packages(self):
        return self.shell.run(["pm", "list", "packages"], check=True).stdout.splitlines()


class IntentService:
    def __init__(self, shell: ShellService):
        self.shell = shell

    def launch(self, package: str, uri: str):
        return self.shell.run([
            "am", "start",
            "-a", "android.intent.action.VIEW",
            "-p", package,
            "-d", uri
        ])


class LogcatService:
    def __init__(self, shell: ShellService):
        self.shell = shell

    def clear(self):
        return self.shell.run(["logcat", "-c"])


class AndroidPlatform:
    def __init__(self):
        self.shell = ShellService()
        self.process = ProcessService(self.shell)
        self.package = PackageService(self.shell)
        self.intent = IntentService(self.shell)
        self.logcat = LogcatService(self.shell)
