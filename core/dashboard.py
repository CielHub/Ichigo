
"""
dashboard.py
CARRERA-HUB v2
Enhanced Color Dashboard
"""

from __future__ import annotations

import os
import shutil
import time

class C:
    RESET="\033[0m"
    RED="\033[91m"
    GREEN="\033[92m"
    YELLOW="\033[93m"
    BLUE="\033[94m"
    CYAN="\033[96m"
    MAGENTA="\033[95m"
    WHITE="\033[97m"
    BOLD="\033[1m"

def color_status(state:str):
    s=state.upper()
    if s in ("ONLINE","SUCCESS","HEALTHY"):
        return C.GREEN+s+C.RESET
    if s in ("RECOVERY","RECOVERING","WARNING"):
        return C.YELLOW+s+C.RESET
    if s in ("OFFLINE","FAILED","ERROR"):
        return C.RED+s+C.RESET
    return C.WHITE+s+C.RESET

class DashboardEngine:

    def __init__(self,config,state,logger,recovery_scheduler):
        self.config=config
        self.state=state
        self.logger=logger
        self.scheduler=recovery_scheduler

    def clear(self):
        os.system("clear")

    def line(self,w):
        return "═"*w

    def header(self):
        width=max(70,shutil.get_terminal_size((100,30)).columns)
        print(C.CYAN+"╔"+self.line(width-2)+"╗"+C.RESET)
        title=" CARRERA-HUB v2.0 "
        print(C.CYAN+"║"+C.BOLD+title.center(width-2)+C.RESET+C.CYAN+"║"+C.RESET)
        print(C.CYAN+"╚"+self.line(width-2)+"╝"+C.RESET)

    def runtime_panel(self):
        snap=self.state.snapshot()

        print(C.BLUE+"┌──────────── Runtime ────────────┐"+C.RESET)
        print(f" {C.BOLD}Updated{C.RESET}      : {time.strftime('%H:%M:%S')}")
        print(f" {C.BOLD}Packages{C.RESET}     : {len(snap['packages'])}")
        print(f" {C.BOLD}Recovery Q{C.RESET}   : {self.scheduler.queue_size()}")
        print(f" {C.BOLD}Running Rec{C.RESET}  : {len(self.scheduler.running_packages())}")
        print(C.BLUE+"└─────────────────────────────────┘"+C.RESET)

    def package_table(self):
        snap=self.state.snapshot()

        print()
        print(C.MAGENTA+"┌────┬──────────────────────────┬────────────┬─────────┬────────┐"+C.RESET)
        print("│ ID │ Package                  │ Status     │ Error   │ PID    │")
        print(C.MAGENTA+"├────┼──────────────────────────┼────────────┼─────────┼────────┤"+C.RESET)

        for idx,(pkg,ctx) in enumerate(snap["packages"].items(),1):
            state=getattr(getattr(ctx,"state",None),"name","UNKNOWN")
            err=getattr(ctx,"current_error","-") or "-"
            pid=str(getattr(ctx,"pid","-"))
            print(
                f"│ {idx:<2} │ "
                f"{pkg[:24]:<24} │ "
                f"{color_status(state):<21}"
                f"│ {str(err):<7} │ "
                f"{pid[:6]:<6} │"
            )

        print(C.MAGENTA+"└────┴──────────────────────────┴────────────┴─────────┴────────┘"+C.RESET)

    def footer(self):
        print()
        print(C.CYAN+"F1"+C.RESET+" Dashboard   "
              +C.GREEN+"F2"+C.RESET+" Start   "
              +C.RED+"F3"+C.RESET+" Stop   "
              +C.YELLOW+"F4"+C.RESET+" Refresh")

    def render(self):
        self.clear()
        self.header()
        self.runtime_panel()
        self.package_table()
        self.footer()

    def loop(self):
        rate=self.config.get("dashboard","refresh_rate",default=1)
        while True:
            self.render()
            time.sleep(rate)
            
