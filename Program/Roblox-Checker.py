from Config.Util import *
from Config.Config import *

class RobloxChecker:
    def start(self):
        Title("Roblox Checker")
        print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Roblox Checker is currently under development.")
        
        input(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Press Enter to return..." + reset)

if __name__ == "__main__":
    tool = RobloxChecker()
    tool.start()
