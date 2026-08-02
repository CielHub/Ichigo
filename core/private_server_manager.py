
"""
private_server_manager.py
CARRERA-HUB v2
Phase 3.6 - Private Server Manager
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class PrivateServerConfig:
    original_link: str = ""
    deep_link: str = ""
    valid: bool = False


class PrivateServerManager:

    ROBLOX_SCHEMES = ("https", "http", "roblox")

    def __init__(self, config_manager, logger=None):
        self.config = config_manager
        self.logger = logger
        self.data = PrivateServerConfig()

    def validate(self, link: str) -> bool:
        try:
            parsed = urlparse(link)
            if parsed.scheme not in self.ROBLOX_SCHEMES:
                return False

            text = link.lower()
            return (
                "roblox" in text or
                "private" in text or
                "share?code=" in text or
                parsed.scheme == "roblox"
            )
        except Exception:
            return False

    def build_deep_link(self, link: str) -> str:
        """
        Placeholder.
        Future revisions can normalize multiple Roblox URL formats
        into a single deep link representation.
        """
        return link.strip()

    def set_link(self, link: str) -> bool:
        if not self.validate(link):
            self.data.valid = False
            return False

        self.data.original_link = link.strip()
        self.data.deep_link = self.build_deep_link(link)
        self.data.valid = True

        self.save()

        if self.logger:
            self.logger.info("[PRIVATE_SERVER] Link updated")

        return True

    def clear(self):
        self.data = PrivateServerConfig()
        self.save()

    def save(self):
        try:
            self.config.set("roblox", "private_server_link",
                            self.data.original_link)
            self.config.set("roblox", "private_server_deeplink",
                            self.data.deep_link)
            self.config.save()
        except Exception:
            pass

    def load(self):
        try:
            link = self.config.get(
                "roblox",
                "private_server_link",
                default=""
            )
            if link:
                self.data.original_link = link
                self.data.deep_link = self.build_deep_link(link)
                self.data.valid = self.validate(link)
        except Exception:
            pass

    def interactive(self):
        while True:
            print("\n========== Private Server ==========")
            print(f"Current Link : {self.data.original_link or '-'}")
            print("------------------------------------")
            print("[1] Set Link")
            print("[2] Clear Link")
            print("[3] View Deep Link")
            print("[0] Back")

            choice = input("\nSelect > ").strip()

            if choice == "1":
                link = input("\nPaste Private Server Link\n> ").strip()
                if self.set_link(link):
                    print("\nLink saved successfully.")
                else:
                    print("\nInvalid Roblox Private Server Link.")
                input("\nPress Enter...")
            elif choice == "2":
                self.clear()
                print("\nLink cleared.")
                input("\nPress Enter...")
            elif choice == "3":
                print("\nDeep Link\n")
                print(self.data.deep_link or "-")
                input("\nPress Enter...")
            elif choice == "0":
                return
