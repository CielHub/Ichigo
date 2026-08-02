
"""
private_server_engine.py
CARRERA-HUB v2
Phase 3.5 - Private Server Engine
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from urllib.parse import urlparse


class JoinStatus(Enum):
    IDLE=auto()
    VALIDATING=auto()
    BUILDING_INTENT=auto()
    OPENING=auto()
    WAITING=auto()
    SUCCESS=auto()
    FAILED=auto()


@dataclass
class JoinResult:
    package:str
    success:bool
    status:JoinStatus
    message:str=""
    elapsed:float=0.0


class PrivateServerEngine:
    """
    Handles Roblox Private Server join flow.

    Responsibilities:
    - Validate link
    - Build Android intent
    - Open deep link
    - Retry join
    - Update state
    """

    def __init__(
        self,
        config_manager,
        state_manager,
        android_service,
        logger,
        verification_engine,
    ):
        self.config=config_manager
        self.state=state_manager
        self.android=android_service
        self.logger=logger
        self.verifier=verification_engine
        self._lock=threading.RLock()

    def validate_link(self,link:str)->bool:
        try:
            p=urlparse(link)
            return p.scheme in ("http","https","roblox") and bool(p.netloc or p.path)
        except Exception:
            return False

    def join(self,package:str,link:str|None=None)->JoinResult:
        start=time.time()

        with self._lock:
            if link is None:
                link=self.config.get("roblox","private_server_link",default="")

            if not self.validate_link(link):
                return JoinResult(package,False,JoinStatus.FAILED,"Invalid private server link",time.time()-start)

            try:
                self.logger.info(f"[PRIVATE_SERVER] Opening link for {package}")
            except Exception:
                pass

            result=self.android.intent.open_uri(link)

            if not result.success:
                return JoinResult(package,False,JoinStatus.FAILED,result.stderr,time.time()-start)

            wait=self.config.get("launcher","delay",default=5)
            time.sleep(wait)

            verify=self.verifier.verify(package)

            if not verify.success:
                return JoinResult(package,False,JoinStatus.FAILED,"Verification failed after join",time.time()-start)

            return JoinResult(package,True,JoinStatus.SUCCESS,"Private server joined",time.time()-start)

    def retry_join(self,package:str,retries:int=3)->JoinResult:
        last=None
        for _ in range(retries):
            last=self.join(package)
            if last.success:
                return last
        return last
