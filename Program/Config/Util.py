from .Config import *
try:
    import colorama
    import ctypes
    import subprocess
    import os
    import time
    import sys
    import datetime
    import sys
    import requests
    import random
except Exception as e:
    print(f'Python requirements are not done.')
    input(f'Error: {e}')

color_webhook = 0xa80505
username_webhook = name_tool
avatar_webhook = 'IMG URL'

color = colorama.Fore
red = color.RED
white = color.WHITE
green = color.GREEN
reset = color.RESET
blue = color.BLUE
yellow = color.YELLOW

try: username_pc = os.getlogin()
except: username_pc = "username"

try:
    if sys.platform.startswith("win"):
        os_name = "Windows"
    elif sys.platform.startswith("linux"):
        os_name = "Linux"
    else:
        os_name = "Unknown"
except:
    os_name = "None"

tool_path = os.path.dirname(os.path.abspath(__file__)).split("Program\\")[0].split("Program/")[0].strip()

def current_time_day_hour():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def current_time_hour():
    return datetime.datetime.now().strftime('%H:%M:%S')

BEFORE = f'{blue}[{white}'
AFTER = f'{blue}]'

BEFORE_GREEN = f'{blue}[{white}'
AFTER_GREEN = f'{blue}]'

INPUT = f'{BEFORE}>{AFTER} |'
INFO = f'{BEFORE}!{AFTER} |'
ERROR = f'{BEFORE}x{AFTER} |'
ADD = f'{BEFORE}+{AFTER} |'
WAIT = f'{BEFORE}~{AFTER} |'
NOTE = f'{BEFORE}NOTE{AFTER} |'

GEN_VALID = f'{green}[{white}+{green}] |'
GEN_INVALID = f'{red}[{white}x{red}] |'

INFO_ADD = f'{white}[{blue}+{white}]{blue}'

def Censored(text):
    censored = [ website]
    for censored_text in censored:
        if text in censored:
            print(f'{BEFORE + current_time_hour() + AFTER} {ERROR} Unable to find "{white}{text}{blue}".')
            Continue()
            Reset()
        elif censored_text in text:
            print(f'{BEFORE + current_time_hour() + AFTER} {ERROR} Unable to find "{white}{text}{blue}".')
            Continue()
            Reset()
        else:
            pass

def Title(title):
    if os_name == "Windows":
        ctypes.windll.kernel32.SetConsoleTitleW(f"{name_tool} - v{version_tool} - {title}")
    elif os_name == "Linux":
        sys.stdout.write(f"\x1b]2;{name_tool} - v{version_tool} - {title}\x07")
        
def Clear():
    if os_name == "Windows":
        os.system("cls")
    elif os_name == "Linux":
        os.system("clear")

def Reset():
    if os_name == "Windows":
        file = ['python', os.path.join(tool_path, "main.py")]
        subprocess.run(file)

    elif os_name == "Linux":
        file = ['python3', os.path.join(tool_path, "main.py")]
        subprocess.run(file)

def StartProgram(program):
    if os_name == "Windows":
        file = ['python', os.path.join(tool_path, "Program", program)]
        subprocess.run(file)
        
    elif os_name == "Linux":
        file = ['python3', os.path.join(tool_path, "Program", program)]
        subprocess.run(file)

def Slow(text):
    delai = 0.03
    lignes = text.split('\n')
    for ligne in lignes:
        print(ligne)
        time.sleep(delai)

def Continue():
    input(f"{BEFORE + current_time_hour() + AFTER} {INFO} Press to continue -> " + reset)

def Error(e):
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Error: {white}{e}", reset)
    Continue()
    Reset()

def ErrorChoiceStart():
    print(f"\n{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid Choice !", reset)
    time.sleep(1)

def ErrorChoice():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid Choice !", reset)
    time.sleep(3)
    Reset()

def ErrorId():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid ID !", reset)
    time.sleep(3)
    Reset()

def ErrorUrl():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid URL !", reset)
    time.sleep(3)
    Reset()

def ErrorResponse():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid Response !", reset)
    time.sleep(3)
    Reset()

def ErrorEdge():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Edge not installed or driver not up to date !", reset)
    time.sleep(3)
    Reset()

def ErrorToken():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid Token !", reset)
    time.sleep(3)
    Reset()
    
def ErrorNumber():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid Number !", reset)
    time.sleep(3)
    Reset()

def ErrorWebhook():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid Webhook !", reset)
    time.sleep(3)
    Reset()

def ErrorCookie():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid Cookie !", reset)
    time.sleep(3)
    Reset()

def ErrorUsername():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Invalid Username !", reset)
    time.sleep(3)
    Reset()

def ErrorPlateform():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Unsupported Platform !", reset)
    time.sleep(3)
    Reset()

def ErrorModule(e):
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Error Module: {white}{e}", reset)
    Continue()
    Reset()

def OnlyWindows():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} This function is only available on Windows 10/11 !", reset)
    Continue()
    Reset()

def OnlyLinux():
    print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} This function is only available on Linux !", reset)
    Continue()
    Reset()

def MainColor(text):
    start_color = (450, 3, 3)  
    end_color = (450, 118, 118)

    num_steps = 9

    colors = []
    for i in range(num_steps):
        r = start_color[0] + (end_color[0] - start_color[0]) * i // (num_steps - 1)
        g = start_color[1] + (end_color[1] - start_color[1]) * i // (num_steps - 1)
        b = start_color[2] + (end_color[2] - start_color[2]) * i // (num_steps - 1)
        colors.append((r, g, b))
    
    colors += list(reversed(colors[:-1]))  
    
    gradient_chars = '┴┼┘┤└┐─┬├┌└│]░▒░▒█▓▄▌▀()'
    
    def text_color(r, g, b):
        return f"\033[38;2;{r};{g};{b}m"
       
    lines = text.split('\n')
    num_colors = len(colors)
    
    result = []
    for i, line in enumerate(lines):
        for j, char in enumerate(line):
            if char in gradient_chars:
                color_index = (i + j) % num_colors
                color = colors[color_index]
                result.append(text_color(*color) + char + "\033[0m")
            else:
                result.append(char)
        if i < len(lines) - 1:
            result.append('\n')
    
    return ''.join(result)

def MainColor2(text):
    start_color = (168, 5, 5)  
    end_color = (255, 118, 118)

    num_steps = 9

    colors = []
    for i in range(num_steps):
        r = start_color[0] + (end_color[0] - start_color[0]) * i // (num_steps - 1)
        g = start_color[1] + (end_color[1] - start_color[1]) * i // (num_steps - 1)
        b = start_color[2] + (end_color[2] - start_color[2]) * i // (num_steps - 1)
        colors.append((r, g, b))
    
    colors += list(reversed(colors[:-1]))  
    
    def text_color(r, g, b):
        return f"\033[38;2;{r};{g};{b}m"
       
    lines = text.split('\n')
    num_colors = len(colors)
    
    result = []
    for i, line in enumerate(lines):
        for j, char in enumerate(line):
            color_index = (i + j) % num_colors
            color = colors[color_index]
            result.append(text_color(*color) + char + "\033[0m")
        
        if i < len(lines) - 1:
            result.append('\n')
    
    return ''.join(result)

def ChoiceUserAgent():
    file_user_agent = os.path.join(tool_path, "Headers", "UserAgent.txt")

    with open(file_user_agent, "r", encoding="utf-8") as file:
        lines = file.readlines()

    if lines:
        user_agent = random.choice(lines).strip()
    else:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.120 Safari/537.36"
    
    return user_agent

def CheckWebhook(webhook):
    try:
        response = requests.get(webhook)
        if response.status_code == 200 or response.status_code == "200":
            return True
        else:
            return False
    except:
        return None
