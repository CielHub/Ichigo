
"""
dashboard.py
CARRERA-HUB v2
Advanced Dashboard (Foundation)
"""

from __future__ import annotations

import os
import shutil
import time

CSI="\033["

class Color:
    RESET=CSI+"0m"
    BOLD=CSI+"1m"
    CYAN=CSI+"96m"
    BLUE=CSI+"94m"
    GREEN=CSI+"92m"
    YELLOW=CSI+"93m"
    RED=CSI+"91m"
    MAGENTA=CSI+"95m"
    WHITE=CSI+"97m"

def cstate(s):
    s=str(s).upper()
    if s in ("ONLINE","RUNNING","SUCCESS","HEALTHY"):
        return Color.GREEN+s+Color.RESET
    if s in ("RECOVERING","WARNING","VERIFYING","JOINING"):
        return Color.YELLOW+s+Color.RESET
    if s in ("OFFLINE","FAILED","ERROR","CRITICAL"):
        return Color.RED+s+Color.RESET
    return Color.WHITE+s+Color.RESET


class DashboardEngine:

    def __init__(self,config,state,logger,recovery_scheduler):
        self.config=config
        self.state=state
        self.logger=logger
        self.scheduler=recovery_scheduler

    def _w(self):
        return max(100, shutil.get_terminal_size((100,30)).columns)

    def clear(self):
        os.system("clear")

    def hr(self,ch="═"):
        return ch*(self._w()-2)

    def render_header(self):
        print(Color.CYAN+"╔"+self.hr()+"╗"+Color.RESET)
        print(Color.CYAN+"║"+Color.BOLD+" CARRERA-HUB v2 ".center(self._w()-2)+Color.RESET+Color.CYAN+"║"+Color.RESET)
        print(Color.CYAN+"╠"+self.hr("═")+"╣"+Color.RESET)

    def render_runtime(self):
        runtime=self.state.snapshot()
        print(f"{Color.BOLD}Runtime{Color.RESET}")
        print(f" Time            : {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f" Packages        : {len(runtime.get('packages',{}))}")
        print(f" Recovery Queue  : {self.scheduler.queue_size()}")
        print(f" Running Recovery: {len(self.scheduler.running_packages())}")
        print()

    def render_packages(self):
        snap=self.state.snapshot().get("packages",{})
        print(Color.MAGENTA+"┌────┬────────────────────────────┬────────────┬────────┬──────────┐"+Color.RESET)
        print("│ ID │ Package                    │ Status     │ Error  │ Uptime   │")
        print(Color.MAGENTA+"├────┼────────────────────────────┼────────────┼────────┼──────────┤"+Color.RESET)

        if not snap:
            print("│ -- │ No package loaded.                                              │")
        else:
            for i,(pkg,obj) in enumerate(snap.items(),1):
                st=getattr(getattr(obj,"state",None),"name","UNKNOWN")
                err=str(getattr(obj,"current_error","-") or "-")
                up=str(getattr(obj,"uptime","-"))
                print(f"│ {i:<2} │ {pkg[:26]:<26} │ {cstate(st):<20}│ {err[:6]:<6} │ {up[:8]:<8} │")

        print(Color.MAGENTA+"└────┴────────────────────────────┴────────────┴────────┴──────────┘"+Color.RESET)

    def render_scheduler(self):
        print()
        print(Color.BLUE+"Scheduler"+Color.RESET)
        print(f" Queue Size : {self.scheduler.queue_size()}")
        print(f" Running    : {', '.join(self.scheduler.running_packages()) or '-'}")

    def render_footer(self):
        print()
        print(Color.CYAN+"────────────────────────────────────────────────────────────────────────────"+Color.RESET)
        print(Color.GREEN+"F1"+Color.RESET+" Dashboard   "
              +Color.YELLOW+"F2"+Color.RESET+" Refresh   "
              +Color.BLUE+"F3"+Color.RESET+" Menu   "
              +Color.RED+"F4"+Color.RESET+" Exit")

    def render(self):
        self.clear()
        self.render_header()
        self.render_runtime()
        self.render_packages()
        self.render_scheduler()
        self.render_footer()

    def loop(self):
        interval=self.config.get("dashboard","refresh_rate",default=1)
        while True:
            self.render()
            time.sleep(interval)
        
