
"""
menu.py
CARRERA-HUB v2
Phase 3.6 - Terminal Menu
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Dict, Optional


@dataclass
class MenuItem:
    key: str
    title: str
    action: Optional[Callable] = None


class MenuEngine:

    def __init__(self, app=None):
        self.app = app
        self.running = True
        self.items: Dict[str, MenuItem] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("1", "▶ Start Auto Rejoin System", self._start)
        self.register("2", "■ Stop Runtime", self._stop)
        self.register("3", "📊 Dashboard", self._dashboard)
        self.register("4", "📦 Package Manager", self._package_manager)
        self.register("5", "🔗 Private Server")
        self.register("6", "⚙ Settings")
        self.register("7", "🩺 Diagnostics")
        self.register("8", "📜 Logs")
        self.register("9", "ℹ About", self._about)
        self.register("0", "✖ Exit", self._exit)

    def register(self, key: str, title: str, action: Callable | None = None):
        self.items[key] = MenuItem(key, title, action)

    def clear(self):
        os.system("clear")

    def render(self):
        self.clear()
        print("╔══════════════════════════════════════════════╗")
        print("║              CARRERA-HUB v2.0               ║")
        print("╚══════════════════════════════════════════════╝")
        print()
        print("┌──────────────── Main Menu ────────────────┐")
        print("│                                           │")
        for key in sorted(self.items.keys()):
            item = self.items[key]
            text = f"  [{item.key}] {item.title}"
            print(f"│ {text:<41}│")
        print("│                                           │")
        print("└───────────────────────────────────────────┘")
        print()

    def loop(self):
        while self.running:
            self.render()
            choice = input("Select > ").strip()
            item = self.items.get(choice)
            if not item:
                input("Invalid selection. Press Enter...")
                continue
            if item.action:
                item.action()
            else:
                input("Feature not implemented yet. Press Enter...")

    def _start(self):
        if self.app:
            self.app.start()
        input("Runtime started. Press Enter...")

    def _stop(self):
        if self.app:
            self.app.stop()
        input("Runtime stopped. Press Enter...")

    def _dashboard(self):
        if self.app and hasattr(self.app, "dashboard"):
            self.app.dashboard.render()
        input("\nPress Enter to return...")

    def _package_manager(self):
        print("\nPackage Manager will be implemented in a later phase.")
        input("\nPress Enter to return...")

    def _about(self):
        print("\nCARRERA-HUB v2")
        print("Production Auto Rejoin System")
        print("Android 10 + Termux + Root")
        input("\nPress Enter to return...")

    def _exit(self):
        self.running = False
