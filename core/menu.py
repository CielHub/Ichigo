
"""
menu.py
CARRERA-HUB v2
Revised Menu Engine
"""

from __future__ import annotations
import os

class MenuEngine:
    def __init__(self, app=None):
        self.app=app
        self.running=True

    def clear(self):
        os.system("clear")

    def draw(self):
        self.clear()
        print("╔══════════════════════════════════════════════╗")
        print("║              CARRERA-HUB v2.0               ║")
        print("╚══════════════════════════════════════════════╝")
        print()
        print(" [1] 📦 Scan Roblox Packages")
        print(" [2] 🔗 Private Server")
        print(" [3] ▶ Start Auto Rejoin")
        print(" [4] 📊 Dashboard")
        print(" [5] ⚙ Settings")
        print(" [6] 🩺 Diagnostics")
        print(" [7] 📜 Logs")
        print(" [8] ℹ About")
        print()
        print(" [0] ✖ Exit")
        print()

    def loop(self):
        while self.running:
            self.draw()
            choice=input("Select > ").strip()

            if choice=="1":
                self.scan_packages()
            elif choice=="2":
                self.private_server()
            elif choice=="3":
                self.start_runtime()
            elif choice=="4":
                self.dashboard()
            elif choice=="5":
                self.placeholder("Settings")
            elif choice=="6":
                self.placeholder("Diagnostics")
            elif choice=="7":
                self.placeholder("Logs")
            elif choice=="8":
                self.about()
            elif choice=="0":
                self.running=False

    def scan_packages(self):
        if self.app and hasattr(self.app,"package_manager"):
            self.app.package_manager.interactive()
        else:
            self.placeholder("Package Manager")

    def private_server(self):
        if self.app and hasattr(self.app,"private_server_manager"):
            self.app.private_server_manager.interactive()
        else:
            self.placeholder("Private Server Manager")

    def start_runtime(self):
        if self.app:
            self.app.start()
        input("\nRuntime started. Press Enter...")

    def dashboard(self):
        if self.app and hasattr(self.app,"dashboard"):
            self.app.dashboard.render()
        input("\nPress Enter to return...")

    def about(self):
        print("\nCARRERA-HUB v2")
        print("Android 10 + Termux + Root")
        print("Multi-instance Roblox Auto Rejoin")
        input("\nPress Enter...")

    def placeholder(self,name):
        print(f"\n{name} belum diimplementasikan.")
        input("\nPress Enter...")
        
