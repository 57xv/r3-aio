from Program.Config.Config import *
from Program.Config.Util import *

try:
   from Program.Config.RPC import rpc
except ImportError:
   print(f"{red}[!] Failed to import pypresence. RPC will be disabled.{reset}")
   print(f"{red}[!] Please run: pip install pypresence{reset}")
   time.sleep(3)
   class DummyRPC:
      def connect(self): pass
      def update(self, **kwargs): pass
      def close(self): pass
   rpc = DummyRPC()

try:
   import webbrowser
   import re
   import pyzipper
   from tkinter import messagebox
   rpc.connect()
except Exception as e:
   print(f"{red}[!] RPC Main Error: {e}{reset}")
   ErrorModule(e)





option_01 = "Facebook-Bypasser"
option_02 = "Xbox-Bypasser"
option_03 = "Google-Bypasser"
option_04 = "Nintendo-Bypasser"
option_05 = "Soon"
option_06 = "Soon"
option_07 = "Soon"
option_08 = "Soon"
option_09 = "Soon"

option_10 = "Xbox-Follower"
option_11 = "Code-Puller"
option_12 = "Code-Checker"
option_13 = "Soon"
option_14 = "Soon"
option_15 = "Soon"
option_16 = "Soon"
option_17 = "Soon"
option_18 = "Soon"
option_19 = "Soon"

option_20 = "Roblox-Checker"
option_21 = "Fortnite-Checker"
option_22 = "Hotmail-Checker"
option_23 = "Disney-Checker"
option_24 = "IMAP-Checker"
option_25 = "Soon"
option_26 = "Soon"
option_27 = "Soon"
option_28 = "Soon"
option_29 = "Soon"

option_99 = "Settings"


option_next = "Next"
option_back = "Back"
option_site = "Site"
option_info = "Info"

option_01_txt = f"{blue}[{white}01{blue}]{white} " + option_01.ljust(23)[:23].replace("-", " ")
option_02_txt = f"{blue}[{white}02{blue}]{white} " + option_02.ljust(23)[:23].replace("-", " ")
option_03_txt = f"{blue}[{white}03{blue}]{white} " + option_03.ljust(23)[:23].replace("-", " ")
option_04_txt = f"{blue}[{white}04{blue}]{white} " + option_04.ljust(23)[:23].replace("-", " ")
option_05_txt = f"{blue}[{white}05{blue}]{white} " + option_05.ljust(23)[:23].replace("-", " ")
option_06_txt = f"{blue}[{white}06{blue}]{white} " + option_06.ljust(23)[:23].replace("-", " ")
option_07_txt = f"{blue}[{white}07{blue}]{white} " + option_07.ljust(23)[:23].replace("-", " ")
option_08_txt = f"{blue}[{white}08{blue}]{white} " + option_08.ljust(23)[:23].replace("-", " ")
option_09_txt = f"{blue}[{white}09{blue}]{white} " + option_09.ljust(23)[:23].replace("-", " ")

option_10_txt = f"{blue}[{white}10{blue}]{white} " + option_10.ljust(23)[:23].replace("-", " ")
option_11_txt = f"{blue}[{white}11{blue}]{white} " + option_11.ljust(23)[:23].replace("-", " ")
option_12_txt = f"{blue}[{white}12{blue}]{white} " + option_12.ljust(23)[:23].replace("-", " ")
option_13_txt = f"{blue}[{white}13{blue}]{white} " + option_13.ljust(23)[:23].replace("-", " ")
option_14_txt = f"{blue}[{white}14{blue}]{white} " + option_14.ljust(23)[:23].replace("-", " ")
option_15_txt = f"{blue}[{white}15{blue}]{white} " + option_15.ljust(23)[:23].replace("-", " ")
option_16_txt = f"{blue}[{white}16{blue}]{white} " + option_16.ljust(23)[:23].replace("-", " ")
option_17_txt = f"{blue}[{white}17{blue}]{white} " + option_17.ljust(23)[:23].replace("-", " ")
option_18_txt = f"{blue}[{white}18{blue}]{white} " + option_18.ljust(23)[:23].replace("-", " ")
option_19_txt = f"{blue}[{white}19{blue}]{white} " + option_19.ljust(23)[:23].replace("-", " ")

option_20_txt = f"{blue}[{white}20{blue}]{white} " + option_20.ljust(23)[:23].replace("-", " ")
option_21_txt = f"{blue}[{white}21{blue}]{white} " + option_21.ljust(23)[:23].replace("-", " ")
option_22_txt = f"{blue}[{white}22{blue}]{white} " + option_22.ljust(23)[:23].replace("-", " ")
option_23_txt = f"{blue}[{white}23{blue}]{white} " + option_23.ljust(23)[:23].replace("-", " ")
option_24_txt = f"{blue}[{white}24{blue}]{white} " + option_24.ljust(23)[:23].replace("-", " ")
option_25_txt = f"{blue}[{white}25{blue}]{white} " + option_25.ljust(23)[:23].replace("-", " ")
option_26_txt = f"{blue}[{white}26{blue}]{white} " + option_26.ljust(23)[:23].replace("-", " ")
option_27_txt = f"{blue}[{white}27{blue}]{white} " + option_27.ljust(23)[:23].replace("-", " ")
option_28_txt = f"{blue}[{white}28{blue}]{white} " + option_28.ljust(23)[:23].replace("-", " ")
option_29_txt = f"{blue}[{white}29{blue}]{white} " + option_29.ljust(23)[:23].replace("-", " ")
option_99_txt = f"{blue}[{white}99{blue}]{white} " + option_99.ljust(23)[:23].replace("-", " ")



option_site_txt = f"{blue}[{white}S{blue}]{white} " + option_site.ljust(24)[:24]
option_info_txt =  f"{blue}[{white}I{blue}]{white} " + option_info.ljust(24)[:24]

menu1 = f"""
  {blue}┌────────────────────────────────────────────────────────────────────────────────────────────┐{white}
  {blue}│ {white}Fortnite Tools               {blue}│ {white}Tools                        {blue}│ {white}Checkers                     {blue}│{white}
  {blue}├──────────────────────────────┼──────────────────────────────┼──────────────────────────────┤{white}
  {blue}│ {option_01_txt} {blue}│ {option_10_txt} {blue}│ {option_20_txt} {blue}│{white}
  {blue}│ {option_02_txt} {blue}│ {option_11_txt} {blue}│ {option_21_txt} {blue}│{white}
  {blue}│ {option_03_txt} {blue}│ {option_12_txt} {blue}│ {option_22_txt} {blue}│{white}
  {blue}│ {option_04_txt} {blue}│ {option_13_txt} {blue}│ {option_23_txt} {blue}│{white}
  {blue}│ {option_05_txt} {blue}│ {option_14_txt} {blue}│ {option_24_txt} {blue}│{white}
  {blue}│ {option_06_txt} {blue}│ {option_15_txt} {blue}│ {option_25_txt} {blue}│{white}
  {blue}│ {option_07_txt} {blue}│ {option_16_txt} {blue}│ {option_26_txt} {blue}│{white}
  {blue}│ {option_08_txt} {blue}│ {option_17_txt} {blue}│ {option_27_txt} {blue}│{white}
  {blue}│ {option_09_txt} {blue}│ {option_18_txt} {blue}│ {option_28_txt} {blue}│{white}
  {blue}│                              │ {option_19_txt} {blue}│ {option_29_txt} {blue}│{white}
  {blue}└──────────────────────────────┴──────────────────────────────┴──────────────────────────────┘{white}
  {blue}│ {option_99_txt} {blue}│ {option_info_txt} {blue}│ {option_site_txt} {blue}│{white}
  {blue}└──────────────────────────────┴──────────────────────────────┴──────────────────────────────┘{white}
"""

def Update():
   popup_version = ""
   try:
      new_version = re.search(r'version_tool\s*=\s*"([^"]+)"', requests.get(url_config).text).group(1)
      if new_version != version_tool:
         webbrowser.open(f"https://{github_tool}")
         colorama.init()
         input(f"{BEFORE + current_time_hour() + AFTER} {INFO} Please download the newest version: {white + version_tool + blue} -> {white + new_version} ")
         popup_version = f"{blue}New Version: {white + version_tool + blue} -> {white + new_version}"
         colorama.deinit()
         Clear()
   except: pass

   return popup_version

menu_path = os.path.join(tool_path, "Program", "Config", "Menu.txt")

def Menu():
   popup_version = ""

   try:
      with open(menu_path, "r") as file:
         menu_number = file.read()
      menu_mapping = {"1": menu1}
      menu = menu_mapping.get(menu_number, menu1)
   except:
      menu = menu1
      menu_number = "1"

   banner = f"""
{blue}   ██▀███   ██████    ▄▄▄       ██▓ ▒█████  
{blue}  ▓██ ▒ ██▒▒██    ▒  ▒████▄    ▓██▒▒██▒  ██▒
{blue}  ▓██ ░▄█ ▒░ ▓██▄    ▒██  ▀█▄  ▒██▒▒██░  ██▒
{blue}  ▒██▀▀█▄    ▒   ██▒ ░██▄▄▄▄██ ░██░▒██   ██░
{blue}  ░██▓ ▒██▒▒██████▒▒  ▓█   ▓██▒░██░░ ████▓▒░
{blue}  ░ ▒▓ ░▒▓░▒ ▒▓▒ ▒ ░  ▒▒   ▓▒█░░▓  ░ ▒░▒░▒░ 
{blue}    ░▒ ░ ▒░░ ░▒  ░ ░   ▒   ▒▒ ░ ▒ ░  ░ ▒ ▒░ 
{blue}    ░░   ░ ░  ░  ░     ░   ▒    ▒ ░░ ░ ░ ▒  
{blue}     ░           ░         ░  ░ ░      ░ ░  
                                                
{white}   {gunslol}
{menu}"""
   return banner, menu_number

while True:
   try:
      Clear()

      banner, menu_number = Menu()

      Title(f"Home Page")
      print(banner)

      choice = input(f" {blue}┌──@{white}r3aio {blue}─ {white}home page\n {blue}└─{white}$ ").strip()

      if choice in ['I', 'i', 'INFO', 'Info', 'info']:
         StartProgram(f"{option_info}.py")
         continue

      elif choice in ['S', 's', 'SITE', 'Site', 'site']:
         StartProgram(f"{option_site}.py")
         continue
      

      options = {
         '01': option_01, '02': option_02, '03': option_03, '04': option_04,
         '05': option_05, '06': option_06, '07': option_07, '08': option_08,
         '09': option_09, '10': option_10, '11': option_11, '12': option_12,
         '13': option_13, '14': option_14, '15': option_15, '16': option_16,
         '17': option_17, '18': option_18, '19': option_19, '20': option_20,
         '21': option_21, '22': option_22, '23': option_23, '24': option_24,
         '25': option_25, '26': option_26, '27': option_27, '28': option_28,
         '29': option_29, '99': option_99
      }

      if choice in options:
         tool_name = options[choice].replace("-", " ")
         rpc.update(state=f"Using {tool_name}", small_image="tool")
         StartProgram(f"{options[choice]}.py")
      elif '0' + choice in options:
         tool_name = options['0' + choice].replace("-", " ")
         rpc.update(state=f"Using {tool_name}", small_image="tool")
         StartProgram(f"{options['0' + choice]}.py")
      else:
         ErrorChoiceStart()

   except Exception as e:
      Error(e)
