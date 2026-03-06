from Config.Util import *
from Config.Config import *
try:
    import webbrowser
except Exception as e:
   ErrorModule(e)

Title("Info")

try:
    print(f"\n{BEFORE + current_time_hour() + AFTER} {WAIT} Information Recovery..{reset}")

    Slow(f"""
{white}────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 {INFO_ADD} Project       :  {white}{name_tool}
 {INFO_ADD} Version       :  {white}{version_tool}
 {INFO_ADD} Creator       :  {white}{creator}
 {INFO_ADD} Frozi         :  {white}https://{gunslol}
 {INFO_ADD} GitHub        :  {white}https://{github_tool}
 {INFO_ADD} Telegram      :  {white}https://{telegram}
{white}────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
""")
    Continue()
    Reset()
except Exception as e:
    Error(e)