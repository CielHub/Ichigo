"""
package_registry.py
CARRERA-HUB v2
Phase 3.1 - Package Registry
"""

from __future__ import annotations

import copy
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class PackageRegistryError(Exception):
    pass


@dataclass
class PackageProfile:
    package_name: str
    alias: str = ""
    enabled: bool = True
    priority: int = 0
    private_server: str = ""
    launch_delay: int = 0
    recovery_delay: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


class PackageRegistry:
    """
    Registry for static package information.

    Does NOT store runtime state.
    Runtime data belongs to StateManager.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._packages: Dict[str, PackageProfile] = {}

    def add(self, profile: PackageProfile):
        with self._lock:
            if profile.package_name in self._packages:
                raise PackageRegistryError("Package already exists")
            self._packages[profile.package_name] = profile

    def remove(self, package_name: str):
        with self._lock:
            self._packages.pop(package_name, None)

    def exists(self, package_name: str) -> bool:
        return package_name in self._packages

    def get(self, package_name: str) -> Optional[PackageProfile]:
        return self._packages.get(package_name)

    def all(self) -> Dict[str, PackageProfile]:
        return copy.deepcopy(self._packages)

    def enabled(self) -> List[PackageProfile]:
        return [
            copy.deepcopy(p)
            for p in self._packages.values()
            if p.enabled
        ]

    def disabled(self) -> List[PackageProfile]:
        return [
            copy.deepcopy(p)
            for p in self._packages.values()
            if not p.enabled
        ]

    def set_enabled(self, package_name: str, enabled: bool):
        if package_name in self._packages:
            self._packages[package_name].enabled = enabled

    def update_priority(self, package_name: str, priority: int):
        if package_name in self._packages:
            self._packages[package_name].priority = priority

    def update_private_server(self, package_name: str, link: str):
        if package_name in self._packages:
            self._packages[package_name].private_server = link

    def sorted_packages(self) -> List[PackageProfile]:
        return sorted(
            (copy.deepcopy(x) for x in self._packages.values()),
            key=lambda p: p.priority
        )

    def count(self) -> int:
        return len(self._packages)

    def clear(self):
        with self._lock:
            self._packages.clear()

    def export(self) -> List[dict]:
        return [
            {
                "package_name": p.package_name,
                "alias": p.alias,
                "enabled": p.enabled,
                "priority": p.priority,
                "private_server": p.private_server,
                "launch_delay": p.launch_delay,
                "recovery_delay": p.recovery_delay,
                "tags": list(p.tags),
                "metadata": dict(p.metadata),
            }
            for p in self.sorted_packages()
        ]
