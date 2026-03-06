from Config.Util import *
from Config.Config import *

class HotmailChecker:
    def start(self):
        Title("Hotmail Checker")
        print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Hotmail Checker is currently under development.")
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Please use IMAP Checker (Option 23) for Hotmail/Outlook accounts.")
        
        input(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Press Enter to return..." + reset)

if __name__ == "__main__":
    tool = HotmailChecker()
    tool.start()
