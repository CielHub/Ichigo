
"""
config_manager.py
=================

CARRERA-HUB v2
Phase 3.1 - Core Foundation
"""

from __future__ import annotations

import json
import os
import threading
from copy import deepcopy
from typing import Any


class ConfigManager:
    CONFIG_VERSION = 1

    DEFAULT_CONFIG = {
        "config_version": CONFIG_VERSION,
        "debug": False,
        "launch_timeout": 30,
        "launch_retry": 3,
        "launch_delay": 5,
        "monitor_interval": 15,
        "error_detection_delay": 5,
        "recovery_delay": 15,
        "recovery_cooldown": 30,
        "max_recovery_retry": 3,
        "dashboard_refresh": 1,
        "cache_cleaner_enabled": True,
        "cache_clean_interval": 30,
        "private_server_link": "",
        "packages": [],
    }

    def __init__(self, config_path: str = "config.json"):
        self._config_path = config_path
        self._lock = threading.RLock()
        self._config = deepcopy(self.DEFAULT_CONFIG)

    def load(self) -> None:
        with self._lock:
            if not os.path.exists(self._config_path):
                self.save()
                return

            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                try:
                    os.replace(self._config_path, self._config_path + ".broken")
                except Exception:
                    pass
                self._config = deepcopy(self.DEFAULT_CONFIG)
                self.save()
                return

            self._config.update(data)
            self._migrate()
            self.validate()
            self.save()

    def save(self) -> None:
        with self._lock:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def all(self) -> dict:
        return deepcopy(self._config)

    def validate(self) -> None:
        integer_keys = [
            "launch_timeout",
            "launch_retry",
            "launch_delay",
            "monitor_interval",
            "error_detection_delay",
            "recovery_delay",
            "recovery_cooldown",
            "max_recovery_retry",
            "dashboard_refresh",
            "cache_clean_interval",
        ]

        for key in integer_keys:
            value = self._config.get(key)
            if not isinstance(value, int):
                raise ValueError(f"{key} must be an integer")
            if value < 0:
                raise ValueError(f"{key} cannot be negative")

        if not isinstance(self._config["packages"], list):
            raise ValueError("packages must be a list")

        if not isinstance(self._config["private_server_link"], str):
            raise ValueError("private_server_link must be a string")

    def _migrate(self) -> None:
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = deepcopy(value)
        self._config["config_version"] = self.CONFIG_VERSION
