
"""
dashboard.py
CARRERA-HUB v2
Phase 3.5 - Dashboard Engine (Foundation)
"""

from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass
from typing import List


@dataclass
class DashboardConfig:
    title:str="CARRERA-HUB v2"
    refresh_rate:float=1.0


class BoxRenderer:

    @staticmethod
    def box(title:str, lines:List[str], width:int)->str:
        top="┌"+"─"*(width-2)+"┐"
        head=f"│ {title}".ljust(width-1)+"│"
        sep="├"+"─"*(width-2)+"┤"
        body=[]
        for line in lines:
            body.append(("│ "+line).ljust(width-1)+"│")
        bot="└"+"─"*(width-2)+"┘"
        return "\n".join([top,head,sep,*body,bot])


class TableRenderer:

    @staticmethod
    def packages(rows,width):
        headers=["ID","Package","Status","PID","Health","Error","Uptime"]
        col=[4,24,12,8,10,8,10]
        def fmt(vals):
            out="│"
            for v,w in zip(vals,col):
                out+=f" {str(v)[:w-1]:<{w-1}}│"
            return out
        line="├"+"┼".join("─"*c for c in col)+"┤"
        top="┌"+"┬".join("─"*c for c in col)+"┐"
        bot="└"+"┴".join("─"*c for c in col)+"┘"
        txt=[top,fmt(headers),line]
        for r in rows:
            txt.append(fmt(r))
        txt.append(bot)
        return "\n".join(txt)


class DashboardEngine:

    def __init__(self,config,state,logger,scheduler):
        self.config=config
        self.state=state
        self.logger=logger
        self.scheduler=scheduler
        self.cfg=DashboardConfig()

    def clear(self):
        os.system("clear")

    def _runtime_box(self):
        snap=self.state.snapshot()
        lines=[
            f"Runtime    : {snap['runtime_state']}",
            f"Packages   : {len(snap['packages'])}",
            f"RecoveryQ  : {self.scheduler.queue_size()}",
            f"Terminal   : {shutil.get_terminal_size((80,24)).columns} cols",
            f"Updated    : {time.strftime('%H:%M:%S')}"
        ]
        return BoxRenderer.box(self.cfg.title,lines,70)

    def _package_table(self):
        snap=self.state.snapshot()
        rows=[]
        i=1
        for name,ctx in snap["packages"].items():
            metrics=ctx.metrics if hasattr(ctx,"metrics") else None
            up="-"
            rows.append([
                i,
                name,
                getattr(ctx.state,"name","?"),
                ctx.pid if getattr(ctx,"pid",None) else "-",
                getattr(ctx.health,"name","?"),
                ctx.current_error if getattr(ctx,"current_error",None) else "-",
                up
            ])
            i+=1
        return TableRenderer.packages(rows,120)

    def render(self):
        self.clear()
        print(self._runtime_box())
        print()
        print(self._package_table())

    def loop(self):
        while True:
            self.render()
            time.sleep(self.cfg.refresh_rate)
