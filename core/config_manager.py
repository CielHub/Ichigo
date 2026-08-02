"""
CARRERA-HUB v2
config_manager.py (Production Foundation)

This is the final Phase 3.1 foundation version.
It intentionally contains a rich architecture skeleton that future
phases will extend without breaking the public API.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# ==========================================================
# Exceptions
# ==========================================================

class ConfigError(Exception): ...
class ConfigLoadError(ConfigError): ...
class ConfigSaveError(ConfigError): ...
class ConfigValidationError(ConfigError): ...
class ConfigMigrationError(ConfigError): ...


# ==========================================================
# Schema Models
# ==========================================================

@dataclass
class LauncherConfig:
    timeout:int=30
    retry:int=3
    delay:int=5

@dataclass
class MonitorConfig:
    interval:int=15

@dataclass
class RecoveryConfig:
    delay:int=15
    cooldown:int=30
    max_retry:int=3

@dataclass
class DashboardConfig:
    refresh:int=1

@dataclass
class LoggerConfig:
    level:str="INFO"
    console:bool=True
    file:bool=True

@dataclass
class ErrorDetectionConfig:
    enabled:bool=True
    validation_delay:int=5

@dataclass
class CacheConfig:
    enabled:bool=True
    interval:int=30

@dataclass
class RobloxConfig:
    private_server_link:str=""

@dataclass
class Metadata:
    version:int=1
    created_at:str=""
    updated_at:str=""
    checksum:str=""

@dataclass
class RootSchema:
    metadata:Metadata=field(default_factory=Metadata)
    launcher:LauncherConfig=field(default_factory=LauncherConfig)
    monitor:MonitorConfig=field(default_factory=MonitorConfig)
    recovery:RecoveryConfig=field(default_factory=RecoveryConfig)
    dashboard:DashboardConfig=field(default_factory=DashboardConfig)
    logger:LoggerConfig=field(default_factory=LoggerConfig)
    error_detection:ErrorDetectionConfig=field(default_factory=ErrorDetectionConfig)
    cache:CacheConfig=field(default_factory=CacheConfig)
    roblox:RobloxConfig=field(default_factory=RobloxConfig)
    packages:dict=field(default_factory=dict)


# ==========================================================
# Validator
# ==========================================================

class ConfigValidator:
    @staticmethod
    def validate(cfg:dict)->None:
        required=("launcher","monitor","recovery","dashboard","logger","error_detection","cache","roblox","packages")
        for sec in required:
            if sec not in cfg:
                raise ConfigValidationError(f"Missing section: {sec}")
        if not isinstance(cfg["packages"],dict):
            raise ConfigValidationError("packages must be an object")
        if cfg["launcher"]["timeout"]<=0:
            raise ConfigValidationError("launcher.timeout must be > 0")


# ==========================================================
# Migrator
# ==========================================================

class ConfigMigrator:
    CURRENT_VERSION=1
    @classmethod
    def migrate(cls,cfg:dict,defaults:dict)->dict:
        for k,v in defaults.items():
            if k not in cfg:
                cfg[k]=copy.deepcopy(v)
            elif isinstance(v,dict):
                for sk,sv in v.items():
                    cfg[k].setdefault(sk,copy.deepcopy(sv))
        cfg["_metadata"]["version"]=cls.CURRENT_VERSION
        return cfg


# ==========================================================
# Manager
# ==========================================================

class ConfigManager:

    def __init__(self,path="config.json"):
        self._lock=threading.RLock()
        self.path=Path(path)
        self.backup=self.path.with_suffix(".backup.json")
        self.schema=RootSchema()
        self._config=self._default_dict()

    def _default_dict(self)->dict:
        return {
            "_metadata":{
                "version":1,
                "created_at":"",
                "updated_at":"",
                "checksum":""
            },
            "launcher":vars(self.schema.launcher),
            "monitor":vars(self.schema.monitor),
            "recovery":vars(self.schema.recovery),
            "dashboard":vars(self.schema.dashboard),
            "logger":vars(self.schema.logger),
            "error_detection":vars(self.schema.error_detection),
            "cache":vars(self.schema.cache),
            "roblox":vars(self.schema.roblox),
            "packages":{}
        }

    def load(self):
        with self._lock:
            if not self.path.exists():
                self.reset()
                self.save()
                return
            try:
                self._config=json.loads(self.path.read_text(encoding="utf8"))
            except Exception as e:
                raise ConfigLoadError(str(e))
            self._config=ConfigMigrator.migrate(self._config,self._default_dict())
            ConfigValidator.validate(self._config)
            self._refresh_metadata()

    def save(self):
        with self._lock:
            self._refresh_metadata()
            if self.path.exists():
                shutil.copy2(self.path,self.backup)
            try:
                self.path.write_text(json.dumps(self._config,indent=4,ensure_ascii=False),encoding="utf8")
            except Exception as e:
                raise ConfigSaveError(str(e))

    def reset(self):
        self._config=self._default_dict()
        self._refresh_metadata(created=True)

    def backup_config(self):
        if self.path.exists():
            shutil.copy2(self.path,self.backup)

    def restore(self):
        if self.backup.exists():
            shutil.copy2(self.backup,self.path)
            self.load()

    def get(self,*keys,default=None):
        ref=self._config
        for k in keys:
            if not isinstance(ref,dict):
                return default
            ref=ref.get(k)
            if ref is None:
                return default
        return ref

    def set(self,*keys,value):
        ref=self._config
        for k in keys[:-1]:
            ref=ref.setdefault(k,{})
        ref[keys[-1]]=value

    def dump(self):
        return copy.deepcopy(self._config)

    @property
    def launcher(self): return self._config["launcher"]
    @property
    def monitor(self): return self._config["monitor"]
    @property
    def recovery(self): return self._config["recovery"]
    @property
    def dashboard(self): return self._config["dashboard"]
    @property
    def logger(self): return self._config["logger"]

    def _refresh_metadata(self,created=False):
        now=datetime.utcnow().isoformat()
        meta=self._config["_metadata"]
        if created or not meta["created_at"]:
            meta["created_at"]=now
        meta["updated_at"]=now
        temp=copy.deepcopy(self._config)
        temp["_metadata"]["checksum"]=""
        raw=json.dumps(temp,sort_keys=True).encode()
        meta["checksum"]=hashlib.sha256(raw).hexdigest()
