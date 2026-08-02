
"""
private_server_manager.py
CARRERA-HUB v2
Enhanced Revision
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict,List
from urllib.parse import urlparse


@dataclass
class PrivateServerProfile:
    original_link:str=""
    normalized_link:str=""
    deep_link:str=""
    place_id:str=""
    share_code:str=""
    valid:bool=False


class PrivateServerManager:

    _URL_RE=re.compile(r"roblox|share\?code=",re.I)

    def __init__(self,config_manager,logger=None):
        self.config=config_manager
        self.logger=logger
        self.profile=PrivateServerProfile()
        self._listeners=[]

    def subscribe(self,callback):
        self._listeners.append(callback)

    def _notify(self):
        for cb in list(self._listeners):
            try:
                cb(self.profile)
            except Exception:
                pass

    def validate(self,link:str)->bool:
        try:
            p=urlparse(link)
            if p.scheme not in ("http","https","roblox"):
                return False
            return bool(self._URL_RE.search(link))
        except Exception:
            return False

    def normalize(self,link:str)->str:
        return link.strip()

    def build_deep_link(self,link:str)->str:
        # Foundation only. Future revision converts every supported
        # Roblox URL into a canonical deep link.
        return self.normalize(link)

    def update(self,link:str)->bool:
        if not self.validate(link):
            self.profile.valid=False
            return False

        self.profile.original_link=link.strip()
        self.profile.normalized_link=self.normalize(link)
        self.profile.deep_link=self.build_deep_link(link)
        self.profile.valid=True

        self.save()

        if self.logger:
            self.logger.info("[PS_MANAGER] Private Server updated")

        self._notify()
        return True

    def clear(self):
        self.profile=PrivateServerProfile()
        self.save()
        self._notify()

    def save(self):
        try:
            self.config.set("roblox","private_server_link",self.profile.original_link)
            self.config.set("roblox","normalized_private_server_link",self.profile.normalized_link)
            self.config.set("roblox","private_server_deeplink",self.profile.deep_link)
            self.config.save()
        except Exception:
            pass

    def load(self):
        try:
            link=self.config.get("roblox","private_server_link",default="")
            if link:
                self.update(link)
        except Exception:
            pass

    def export(self)->Dict:
        return {
            "original":self.profile.original_link,
            "normalized":self.profile.normalized_link,
            "deeplink":self.profile.deep_link,
            "valid":self.profile.valid
        }

    def interactive(self):
        while True:
            print("\n========== PRIVATE SERVER ==========")
            print(f"Current : {self.profile.original_link or '-'}")
            print("------------------------------------")
            print("[1] Set / Replace Link")
            print("[2] View Deep Link")
            print("[3] Clear Link")
            print("[4] Validate Current Link")
            print("[0] Back")

            c=input("\nSelect > ").strip()

            if c=="1":
                link=input("\nPaste Roblox Private Server Link\n> ").strip()
                print("\nSaved." if self.update(link) else "\nInvalid link.")
                input("\nPress Enter...")
            elif c=="2":
                print("\nDeep Link:\n")
                print(self.profile.deep_link or "-")
                input("\nPress Enter...")
            elif c=="3":
                self.clear()
                print("\nLink cleared.")
                input("\nPress Enter...")
            elif c=="4":
                print("\nVALID" if self.profile.valid else "\nINVALID")
                input("\nPress Enter...")
            elif c=="0":
                return
                
