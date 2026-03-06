from pypresence import Presence
import time
import threading
from colorama import Fore, Style
from .ConfigManager import config_manager
from .Config import version_tool

class DiscordRPC:
    def __init__(self):
        self.client_id = config_manager.get_setting('discord_app_id', '1466428268378067028')
        self.enabled = config_manager.get_setting('rpc_enabled', True)
        self.rpc = None
        self.connected = False
        self.start_time = None

    def log(self, msg):
        try:
            with open("rpc_log.txt", "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        except:
            pass

    def connect(self):        
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            self.start_time = time.time()
            print(f"{Fore.GREEN}[RPC] Connected!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[RPC] Failed to connect: {e}{Style.RESET_ALL}")
            self.connected = False

    def update(self, state="Idle", details="Main Menu", large_image="omesfnn", small_image=None):
        if not self.enabled:
            return

        # Auto-reconnect if not connected
        if not self.connected:
            try:
                self.connect()
            except:
                pass

        if not self.connected:
            return

        try:
            self.rpc.update(
                state=state,
                details=details,
                start=self.start_time,
                large_image=large_image,
                large_text=f"r3 aio v{version_tool}",
                small_image=small_image
            )
        except Exception as e:
            self.connected = False
            # Try one reconnect immediately
            try:
                self.connect()
                self.rpc.update(
                    state=state,
                    details=details,
                    start=self.start_time,
                    large_image=large_image,
                    large_text=f"r3 aio v{version_tool}",
                    small_image=small_image
                )
            except:
                pass

    def close(self):
        if self.rpc:
            try:
                self.rpc.close()
            except:
                pass

rpc = DiscordRPC()
