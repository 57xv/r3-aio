import re
import json
import time
import random
import os
import threading
import uuid
import sys
import ctypes
import urllib.parse
import requests
from colorama import init, Fore, Style
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import Tk, filedialog
from Config.Util import *
from datetime import datetime

# Initialize Colorama
init(autoreset=True)

# Lock for thread-safe printing and file writing
print_lock = threading.RLock()
file_lock = threading.RLock()

# Configuration
try:
    config_path = os.path.join(os.getcwd(), 'Program', 'Config', 'config.json')
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        MAX_THREADS = int(config_data.get('threads', 50))
        USE_PROXY = config_data.get('proxies_enabled', True)
except Exception:
    MAX_THREADS = 50
    USE_PROXY = True

# Results Directory
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Results', 'Xbox Follower')
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

VALID_FILE = os.path.join(RESULTS_DIR, "followed.txt")
FAILED_FILE = os.path.join(RESULTS_DIR, "failed.txt")
ERROR_LOG_FILE = os.path.join(RESULTS_DIR, "errors.txt")

# Stats
stats = {
    'followed': 0,
    'failed': 0,
    'total': 0
}

def update_title():
    Title(f"Xbox Follower | Target: {TARGET} | Followed: {stats['followed']} | Failed: {stats['failed']} | Threads: {MAX_THREADS}")

def print_hit(email, status):
    with print_lock:
        print(f"{BEFORE + current_time_hour() + AFTER} {GEN_VALID} {white}{email}{reset} | {white}{status}{reset}")

def log_error(email, stage, message):
    with file_lock:
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{current_time_hour()}] {email} | {stage} | {message}\n")

def get_random_proxy(proxies):
    if not proxies:
        return None
    proxy = random.choice(proxies)
    if proxy.count("@") >= 1:
        credentials, addr = proxy.split("@", 1)
        username, password = credentials.split(":", 1)
        proxy_url = f"http://{username}:{password}@{addr}"
    elif proxy.count(':') == 3:
        ip, port, username, password = proxy.split(':')
        proxy_url = f"http://{username}:{password}@{ip}:{port}"
    else:
        proxy_url = f"http://{proxy}"
    
    return {
        'http': proxy_url,
        'https': proxy_url
    }

# ============================================================================
# MICROSOFT OAUTH AUTHENTICATOR (Adapted for curl_cffi)
# ============================================================================
MICROSOFT_OAUTH_URL = 'https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328&redirect_uri=https://login.live.com/oauth20_desktop.srf&scope=service::user.auth.xboxlive.com::MBI_SSL&display=touch&response_type=token&locale=en'

class MicrosoftAuthenticator:
    """Handle Microsoft OAuth authentication"""

    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        })

    def get_oauth_tokens(self):
        """Get OAuth tokens (PPFT and URL POST) from Microsoft"""
        try:
            response = self.session.get(MICROSOFT_OAUTH_URL, timeout=15)
            text = response.text
            
            # Find PPFT token (Robust Regex)
            ppft_match = re.search(r'name="PPFT" id="i0327" value="([^"]+)"', text) or \
                         re.search(r'name="PPFT"[\s\S]*?value="([^"]+)"', text) or \
                         re.search(r'value="([^"]+)"\s+name="PPFT"', text) or \
                         re.search(r'value=\"(.+?)\"', text, re.S) or \
                         re.search(r'value=\\\"(.+?)\\\"', text, re.S)

            if ppft_match:
                ppft_token = ppft_match.group(1)
                
                # Find URL POST
                url_post_match = re.search(r'"urlPost":"([^"]+)"', text) or \
                                 re.search(r'urlPost:\'([^\']+)\'', text) or \
                                 re.search(r'action="([^"]+)"', text) # Fallback to form action

                if url_post_match:
                    url_post = url_post_match.group(1)
                    return (url_post, ppft_token)
            
            return (None, None)
        except Exception:
            return (None, None)

    def login(self, email, password, url_post, ppft_token, max_retries=3):
        """Perform Microsoft login and get RPS token"""
        tries = 0
        while tries < max_retries:
            try:
                data = {
                    'login': email,
                    'loginfmt': email,
                    'passwd': password,
                    'PPFT': ppft_token
                }
                
                login_request = self.session.post(
                    url_post,
                    data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    allow_redirects=True,
                    timeout=15
                )
                
                # Check if token is in URL fragment
                if '#' in login_request.url:
                    fragment = urllib.parse.urlparse(login_request.url).fragment
                    token = urllib.parse.parse_qs(fragment).get('access_token', ['None'])[0]
                    if token != 'None':
                        return token
                
                # Handle security prompt
                if 'cancel?mkt=' in login_request.text:
                    try:
                        ipt_match = re.search(r'(?<="ipt" value=").+?(?=">)', login_request.text)
                        pprid_match = re.search(r'(?<="pprid" value=").+?(?=">)', login_request.text)
                        uaid_match = re.search(r'(?<="uaid" value=").+?(?=">)', login_request.text)
                        action_match = re.search(r'(?<=id="fmHF" action=").+?(?=" )', login_request.text)
                        
                        if ipt_match and pprid_match and uaid_match and action_match:
                            data = {
                                'ipt': ipt_match.group(),
                                'pprid': pprid_match.group(),
                                'uaid': uaid_match.group()
                            }
                            action_url = action_match.group()
                            
                            ret = self.session.post(action_url, data=data, allow_redirects=True, timeout=15)
                            return_url_match = re.search(r'(?<="recoveryCancel":{"returnUrl":").+?(?=",)', ret.text)
                            
                            if return_url_match:
                                return_url = return_url_match.group()
                                fin = self.session.get(return_url, allow_redirects=True, timeout=15)
                                if '#' in fin.url:
                                    token = urllib.parse.parse_qs(urllib.parse.urlparse(fin.url).fragment).get('access_token', ['None'])[0]
                                    if token != 'None':
                                        return token
                    except Exception:
                        pass
                
                # Check for incorrect password
                if 'password is incorrect' in login_request.text.lower():
                    return None
                
            except Exception:
                pass
            
            tries += 1
            if tries < max_retries:
                time.sleep(1)
        
        return None

    def authenticate(self, email, password):
        """Complete authentication flow"""
        url_post, ppft_token = self.get_oauth_tokens()
        if not url_post or not ppft_token:
            return None
        return self.login(email, password, url_post, ppft_token)

def get_xbox_user_token(session, access_token):
    try:
        url = "https://user.auth.xboxlive.com/user/authenticate"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": access_token
            }
        }
        resp = session.post(url, json=data, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()['Token']
        return None
    except Exception:
        return None

def get_xsts_token(session, user_token):
    try:
        url = "https://xsts.auth.xboxlive.com/xsts/authorize"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [user_token]
            },
            "RelyingParty": "http://xboxlive.com",
            "TokenType": "JWT"
        }
        resp = session.post(url, json=data, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            uhs = data.get('DisplayClaims', {}).get('xui', [{}])[0].get('uhs')
            token = data.get('Token')
            return token, uhs
        return None, None
    except Exception:
        return None, None

def get_xuid_from_gamertag(session, uhs, xsts_token, gamertag):
    """Resolve Gamertag to XUID"""
    try:
        # Check if it's a modern gamertag (Name#1234)
        if '#' in gamertag:
            # For modern gamertags, we need to be careful with encoding
            # But the profile endpoint might expect the raw format or split format
            # Let's try the standard endpoint first with encoded value
            pass
            
        url = "https://profile.xboxlive.com/users/gt({})/profile/settings".format(urllib.parse.quote(gamertag))
        headers = {
            "Authorization": f"XBL3.0 x={uhs};{xsts_token}",
            "x-xbl-contract-version": "2",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        params = {'settings': 'Gamertag'}
        
        resp = session.get(url, headers=headers, params=params, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            # Check if we got any users back
            users = data.get('profileUsers', [])
            if users:
                xuid = users[0].get('id')
                return xuid
                
        # Fallback: Try searching for the user if direct lookup fails
        # This is often needed for modern gamertags
        search_url = "https://peoplehub.xboxlive.com/users/me/people/search"
        headers["x-xbl-contract-version"] = "1"
        search_params = {'q': gamertag, 'maxItems': 1}
        
        resp = session.get(search_url, headers=headers, params=search_params, timeout=10)
        if resp.status_code == 200:
             data = resp.json()
             people = data.get('people', [])
             if people:
                 return people[0].get('xuid')

        return None
    except Exception:
        return None

def follow_target(session, xsts_token, uhs, target_xuid):
    try:
        # Use xuid(...) endpoint which is more reliable than gt(...)
        url = f"https://social.xboxlive.com/users/me/people/xuid({target_xuid})"
        
        headers = {
            "Authorization": f"XBL3.0 x={uhs};{xsts_token}",
            "X-XBL-Contract-Version": "2",
            "Accept-Language": "en-US",
            "Accept": "application/json"
        }
        # PUT request to follow
        resp = session.put(url, headers=headers, data=b"", timeout=10)
        
        if resp.status_code in [200, 201, 202, 204]:
            return True, "Followed"
        else:
            return False, f"Failed {resp.status_code} - {resp.text}"
    except Exception as e:
        return False, str(e)

def worker(account, proxies):
    email, password = account
    proxy = get_random_proxy(proxies) if USE_PROXY else None
    
    try:
        # 1. Login to Microsoft
        session = requests.Session()
        if proxy:
            session.proxies = proxy
            
        authenticator = MicrosoftAuthenticator(session)
        access_token = authenticator.authenticate(email, password)
        
        if not access_token:
            with file_lock:
                stats['failed'] += 1
            log_error(email, "Login", "Failed to get Access Token (Invalid creds or Security Challenge)")
            return

        # 2. Get Xbox User Token
        user_token = get_xbox_user_token(session, access_token)
        if not user_token:
            with file_lock:
                stats['failed'] += 1
            log_error(email, "Xbox User Token", "Failed to exchange Access Token for User Token")
            return

        # 3. Get XSTS Token
        xsts_token, uhs = get_xsts_token(session, user_token)
        if not xsts_token:
            with file_lock:
                stats['failed'] += 1
            log_error(email, "XSTS Token", "Failed to get XSTS Token (Check if account has Xbox profile)")
            return

        # 4. Resolve Target XUID (if not already done globally)
        # We do this per thread OR pass it in. For efficiency, let's resolve it once globally?
        # But we need a valid session. Let's resolve it inside the worker using the first successful account.
        # However, to avoid race conditions, we can just resolve it per worker or use a global cache.
        # Better: Since we have the target gamertag in global TARGET, let's try to resolve it.
        
        target_xuid = get_xuid_from_gamertag(session, uhs, xsts_token, TARGET)
        if not target_xuid:
             with file_lock:
                stats['failed'] += 1
             log_error(email, "Resolve XUID", f"Could not find XUID for gamertag: {TARGET}")
             return

        # 5. Follow Target
        success, msg = follow_target(session, xsts_token, uhs, target_xuid)
        
        if success:
            with file_lock:
                stats['followed'] += 1
                with open(VALID_FILE, 'a') as f:
                    f.write(f"{email}:{password}\n")
            print_hit(email, "Followed Successfully")
        else:
            with file_lock:
                stats['failed'] += 1
                with open(FAILED_FILE, 'a') as f:
                    f.write(f"{email}:{password} | {msg}\n")
            log_error(email, "Follow Target", msg)
            
    except Exception as e:
        with file_lock:
            stats['failed'] += 1
        log_error(email, "Exception", str(e))
    finally:
        update_title()

def main():
    global TARGET, stats
    Title("Xbox Follower")
    Clear()
    
    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Xbox Follower Tool")
    
    # 1. Get Target
    print(f"\n{BEFORE + current_time_hour() + AFTER} {INPUT} Enter Target Gamertag:")
    TARGET = input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} > ").strip()
    
    if not TARGET:
        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No target specified!")
        time.sleep(2)
        return

    # 2. Load Accounts
    print(f"\n{BEFORE + current_time_hour() + AFTER} {WAIT} Select Accounts File...")
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(title="Select Accounts File", filetypes=[("Text Files", "*.txt")])
    root.destroy()
    
    if not file_path:
        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No file selected!")
        time.sleep(2)
        return

    accounts = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if ':' in line:
                parts = line.strip().split(':', 1)
                accounts.append((parts[0].strip(), parts[1].strip()))
    
    stats['total'] = len(accounts)
    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Loaded {len(accounts)} accounts")
    
    # 3. Load Proxies
    proxies = []
    if USE_PROXY:
        try:
            if os.path.exists('proxies.txt'):
                with open('proxies.txt', 'r', encoding='utf-8') as f:
                    proxies = [l.strip() for l in f if l.strip()]
                print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Loaded {len(proxies)} proxies")
            else:
                print(f"{BEFORE + current_time_hour() + AFTER} {INFO} proxies.txt not found, using localhost")
        except Exception:
            pass

    # 4. Start Threads
    print(f"{BEFORE + current_time_hour() + AFTER} {WAIT} Starting threads...")
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(worker, acc, proxies) for acc in accounts]
        for _ in as_completed(futures):
            pass
            
    print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Finished! Followed: {stats['followed']} | Failed: {stats['failed']}")
    input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Press Enter to exit...")

if __name__ == "__main__":
    main()
