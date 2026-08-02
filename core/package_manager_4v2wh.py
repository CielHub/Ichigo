
"""
package_manager.py
CARRERA-HUB v2
Revised Package Manager
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class PackageEntry:
    package_name: str
    alias: str
    version: str = "-"
    enabled: bool = False
    selected: bool = False


class PackageManager:

    ROBLOX_PATTERN = re.compile(r"package:(com\.roblox\.[A-Za-z0-9_]+)")

    def __init__(self, android_service, registry, config, logger=None):
        self.android = android_service
        self.registry = registry
        self.config = config
        self.logger = logger
        self._packages: Dict[str, PackageEntry] = {}
        self._selected: Set[str] = set()

    def scan(self) -> List[PackageEntry]:
        self._packages.clear()

        result = self.android.package.list_packages()
        if not result.success:
            return []

        index = 1
        for line in result.stdout.splitlines():
            m = self.ROBLOX_PATTERN.match(line.strip())
            if not m:
                continue

            pkg = m.group(1)
            self._packages[pkg] = PackageEntry(
                package_name=pkg,
                alias=f"Package {index}"
            )
            index += 1

        if self.logger:
            self.logger.info(
                f"[PACKAGE_MANAGER] Detected {len(self._packages)} package(s)"
            )

        return list(self._packages.values())

    def load_saved_selection(self):
        try:
            saved = self.config.get(
                "packages",
                "selected",
                default=[]
            )
            self._selected = set(saved)
            for pkg in self._selected:
                if pkg in self._packages:
                    self._packages[pkg].selected = True
        except Exception:
            pass

    def save_selection(self):
        try:
            self.config.set(
                "packages",
                "selected",
                sorted(self._selected)
            )
            self.config.save()
        except Exception:
            pass

    def toggle(self, package: str):
        if package not in self._packages:
            return

        entry = self._packages[package]

        if entry.selected:
            entry.selected = False
            self._selected.discard(package)
        else:
            entry.selected = True
            self._selected.add(package)

    def select_all(self):
        for pkg, entry in self._packages.items():
            entry.selected = True
            self._selected.add(pkg)

    def clear_selection(self):
        for entry in self._packages.values():
            entry.selected = False
        self._selected.clear()

    def apply(self):
        from core.package_registry import PackageProfile

        self.registry.clear()

        priority = 1
        for pkg in sorted(self._selected):
            self.registry.add(
                PackageProfile(
                    package_name=pkg,
                    alias=f"Package {priority}",
                    enabled=True,
                    priority=priority,
                )
            )
            priority += 1

        self.save_selection()

    def render(self):
        print("\nDetected Roblox Packages\n")
        print(" ID  Sel  Alias        Package")
        print("-" * 70)

        for idx, entry in enumerate(self._packages.values(), start=1):
            mark = "✓" if entry.selected else " "
            print(
                f" {idx:<2}  [{mark}] {entry.alias:<11}"
                f"{entry.package_name}"
            )

        print("\n[A] Select All")
        print("[C] Clear Selection")
        print("[R] Re-scan")
        print("[D] Done")
        print("[B] Back")

    def interactive(self):
        self.scan()
        self.load_saved_selection()

        while True:
            self.render()
            choice = input("\nSelect > ").strip().lower()

            if choice == "a":
                self.select_all()
            elif choice == "c":
                self.clear_selection()
            elif choice == "r":
                self.scan()
                self.load_saved_selection()
            elif choice == "d":
                self.apply()
                print("\nSelection saved.")
                input("Press Enter...")
                return
            elif choice == "b":
                return
            elif choice.isdigit():
                idx = int(choice) - 1
                values = list(self._packages.values())
                if 0 <= idx < len(values):
                    self.toggle(values[idx].package_name)
