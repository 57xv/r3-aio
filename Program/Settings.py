from Config.Util import *
from Config.ConfigManager import config_manager
import time

def Settings():
    Title("Settings")
    
    while True:
        Clear()
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Settings Menu")
        print(f"")
        
        current_threads = config_manager.get_setting('threads')
        current_proxies = config_manager.get_setting('proxies_enabled')
        
        print(f"{blue}[{white}1{blue}] {white}Threads: {blue}{current_threads}")
        print(f"{blue}[{white}2{blue}] {white}Proxies Enabled: {blue}{current_proxies}")
        print(f"{blue}[{white}0{blue}] {white}Back to Menu")
        print(f"")
        
        choice = input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Select option: ")
        
        if choice == '1':
            try:
                print(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Enter new thread count (1-200):")
                new_threads = int(input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} > "))
                if 1 <= new_threads <= 200:
                    config_manager.set_setting('threads', new_threads)
                    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Threads updated to {new_threads}")
                else:
                    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid number (1-200)")
            except ValueError:
                print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid input")
            time.sleep(1)
            
        elif choice == '2':
            new_val = not current_proxies
            config_manager.set_setting('proxies_enabled', new_val)
            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Proxies enabled set to {new_val}")
            time.sleep(1)
            
        elif choice == '0':
            break
            
        else:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid choice")
            time.sleep(1)

    Reset()

if __name__ == "__main__":
    Settings()
