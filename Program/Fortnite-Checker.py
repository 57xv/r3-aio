from Config.Util import *
from Config.Config import *
import time

class FortniteChecker:
    def start(self):
        Title("Fortnite Checker")
        print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Fortnite Checker is currently under development.")
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} This feature will be available in a future update.")
        
        input(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Press Enter to return..." + reset)

if __name__ == "__main__":
    tool = FortniteChecker()
    tool.start()
